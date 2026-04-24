import {
    createConnection,
    TextDocuments,
    ProposedFeatures,
    InitializeParams,
    DidChangeConfigurationNotification,
    CompletionItem,
    CompletionItemKind,
    TextDocumentPositionParams,
    TextDocumentSyncKind,
    InitializeResult,
    Hover,
    MarkupKind
} from 'vscode-languageserver/node';

import {
    TextDocument
} from 'vscode-languageserver-textdocument';

import * as fs from 'fs';
import * as path from 'path';
import { pathToFileURL, fileURLToPath } from 'url';

// Create a connection for the server, using Node's IPC as a transport.
const connection = createConnection(ProposedFeatures.all);

// Create a simple text document manager.
const documents: TextDocuments<TextDocument> = new TextDocuments(TextDocument);

let hasConfigurationCapability = false;
let hasWorkspaceFolderCapability = false;

connection.onInitialize((params: InitializeParams) => {
    connection.console.log('DASM Language Server initializing...');
    const capabilities = params.capabilities;

    // Does the client support the `workspace/configuration` request?
    hasConfigurationCapability = !!(
        capabilities.workspace && !!capabilities.workspace.configuration
    );
    hasWorkspaceFolderCapability = !!(
        capabilities.workspace && !!capabilities.workspace.workspaceFolders
    );

    const result: InitializeResult = {
        capabilities: {
            textDocumentSync: TextDocumentSyncKind.Incremental,
            // Tell the client that this server supports code completion.
            completionProvider: {
                resolveProvider: true
            },
            hoverProvider: true
        }
    };
    if (hasWorkspaceFolderCapability) {
        result.capabilities.workspace = {
            workspaceFolders: {
                supported: true
            }
        };
    }
    
    connection.console.log('DASM Language Server initialized with capabilities: ' + JSON.stringify(result.capabilities));
    return result;
});

connection.onInitialized(() => {
    if (hasConfigurationCapability) {
        // Register for all configuration changes.
        connection.client.register(DidChangeConfigurationNotification.type, undefined);
    }
    if (hasWorkspaceFolderCapability) {
        connection.workspace.onDidChangeWorkspaceFolders((event: any) => {
            connection.console.log('Workspace folder change event received.');
        });
    }

    // Scan all .asm/.dasm files in workspace folders on startup
    if (hasWorkspaceFolderCapability) {
        connection.workspace.getWorkspaceFolders().then(folders => {
            if (!folders) return;
            for (const folder of folders) {
                const folderPath = fileURLToPath(folder.uri);
                scanWorkspaceFiles(folderPath);
            }
        });
    }
});

// Recursively find and parse all .asm/.dasm files in a directory
function scanWorkspaceFiles(dir: string): void {
    let entries: fs.Dirent[];
    try {
        entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
        return;
    }
    for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) {
            // Skip node_modules and hidden directories
            if (entry.name === 'node_modules' || entry.name.startsWith('.')) continue;
            scanWorkspaceFiles(fullPath);
        } else if (entry.isFile() && (entry.name.endsWith('.asm') || entry.name.endsWith('.dasm'))) {
            try {
                const content = fs.readFileSync(fullPath, 'utf8');
                const uri = pathToFileURL(fullPath).toString();
                parseRegisterAnnotations(content, uri);
                connection.console.log(`Scanned workspace file: ${fullPath}`);
            } catch {
                // ignore unreadable files
            }
        }
    }
}

// Interface for storing label information
interface LabelInfo {
    name: string;
    registers: Array<{ register: string; description: string }>;
    line: number;
    document: string;
}

// Store for all labels found in documents
const labelStore: Map<string, LabelInfo> = new Map();

// Function to parse register annotations
function parseRegisterAnnotations(text: string, documentUri: string): void {
    const lines = text.split('\n');
    // Don't clear the entire store, just clear entries for this document
    const keysToDelete: string[] = [];
    labelStore.forEach((value, key) => {
        if (value.document === documentUri) {
            keysToDelete.push(key);
        }
    });
    keysToDelete.forEach(key => labelStore.delete(key));
    
    let currentRegisters: Array<{ register: string; description: string }> = [];
    
    connection.console.log(`Parsing document: ${documentUri}`);
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        
        // Check for register annotation: @REG: Description
        const registerMatch = line.match(/^@([A-Z]{3}):\s*(.*)$/);
        if (registerMatch) {
            const register = registerMatch[1];
            const description = registerMatch[2];
            currentRegisters.push({ register, description });
            connection.console.log(`Found register annotation: ${register} -> ${description}`);
            continue;
        }
        
        // Check for label definition
        const labelMatch = line.match(/^([a-zA-Z_][a-zA-Z0-9_.]*):.*$/);
        if (labelMatch) {
            const labelName = labelMatch[1];
            
            // Store the label with its register annotations
            labelStore.set(labelName, {
                name: labelName,
                registers: [...currentRegisters], // Copy the current registers
                line: i,
                document: documentUri
            });
            
            connection.console.log(`Stored label: ${labelName} with ${currentRegisters.length} registers`);
            
            // Reset registers for next label
            currentRegisters = [];
        }
        
        // If we hit a non-comment, non-register-annotation, non-label line, reset registers
        if (!line.startsWith(';') && !line.startsWith('@') && !line.match(/^[a-zA-Z_][a-zA-Z0-9_.]*:/) && line.length > 0) {
            if (currentRegisters.length > 0) {
                connection.console.log(`Resetting ${currentRegisters.length} unused register annotations`);
            }
            currentRegisters = [];
        }
    }
    
    connection.console.log(`Total labels stored: ${labelStore.size}`);
}

// Update labels when document changes
documents.onDidChangeContent((change: any) => {
    parseRegisterAnnotations(change.document.getText(), change.document.uri);
});

// Update labels when document is opened
documents.onDidOpen((event: any) => {
    parseRegisterAnnotations(event.document.getText(), event.document.uri);
});

// Provide hover information
connection.onHover((textDocumentPosition: TextDocumentPositionParams): Hover | undefined => {
    const document = documents.get(textDocumentPosition.textDocument.uri);
    if (!document) {
        connection.console.log('Document not found');
        return undefined;
    }

    const text = document.getText();
    const lines = text.split('\n');
    const line = lines[textDocumentPosition.position.line];
    
    if (!line) {
        connection.console.log('Line not found');
        return undefined;
    }

    connection.console.log(`Hover on line: "${line}" at position ${textDocumentPosition.position.character}`);

    // Get the word at the current position using a more robust method
    const position = textDocumentPosition.position;
    const lineText = line;
    
    // Find word boundaries
    let start = position.character;
    let end = position.character;
    
    // Move start backwards to find word start
    while (start > 0 && /[a-zA-Z0-9_.]/.test(lineText[start - 1])) {
        start--;
    }
    
    // Move end forwards to find word end
    while (end < lineText.length && /[a-zA-Z0-9_.]/.test(lineText[end])) {
        end++;
    }
    
    const wordAtPosition = lineText.substring(start, end);
    connection.console.log(`Word at position: "${wordAtPosition}"`);
    
    if (!wordAtPosition) {
        connection.console.log('No word found at position');
        return undefined;
    }

    // Log all stored labels for debugging
    connection.console.log(`Stored labels: ${Array.from(labelStore.keys()).join(', ')}`);

    // Check if this word is a label we have information about.
    // Also handle namespace-qualified references like "Video.PackPixel" by
    // falling back to the unqualified name after the last dot.
    let labelInfo = labelStore.get(wordAtPosition);
    if (!labelInfo && wordAtPosition.includes('.')) {
        const unqualified = wordAtPosition.substring(wordAtPosition.lastIndexOf('.') + 1);
        labelInfo = labelStore.get(unqualified);
    }
    connection.console.log(`Label info found for "${wordAtPosition}": ${labelInfo ? 'yes' : 'no'}`);
    
    if (labelInfo && labelInfo.registers.length > 0) {
        let hoverText = `**${labelInfo.name}**\n\n`;
        for (const reg of labelInfo.registers) {
            hoverText += `**${reg.register}**: ${reg.description}  \n`;
        }

        connection.console.log(`Returning hover text: ${hoverText}`);

        return {
            contents: {
                kind: MarkupKind.Markdown,
                value: hoverText
            }
        };
    }

    connection.console.log('No label info found or no registers');
    return undefined;
});

// Provide completion items (optional, for autocompleting label names)
connection.onCompletion(
    (_textDocumentPosition: TextDocumentPositionParams): CompletionItem[] => {
        const completionItems: CompletionItem[] = [];
        
        labelStore.forEach((labelInfo, labelName) => {
            const item: CompletionItem = {
                label: labelName,
                kind: CompletionItemKind.Function,
                detail: `Label with ${labelInfo.registers.length} register annotation(s)`,
                documentation: labelInfo.registers.map(r => `${r.register}: ${r.description}`).join('\n')
            };
            completionItems.push(item);
        });

        return completionItems;
    }
);

connection.onCompletionResolve((item: CompletionItem): CompletionItem => {
    return item;
});

// Make the text document manager listen on the connection
documents.listen(connection);

// Listen on the connection
connection.listen();