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
    MarkupKind,
    Diagnostic,
    DiagnosticSeverity,
    DiagnosticTag
} from 'vscode-languageserver/node';

import {
    TextDocument
} from 'vscode-languageserver-textdocument';

import * as fs from 'fs';
import * as path from 'path';
import { pathToFileURL, fileURLToPath } from 'url';

const connection = createConnection(ProposedFeatures.all);
const documents: TextDocuments<TextDocument> = new TextDocuments(TextDocument);

let hasConfigurationCapability = false;
let hasWorkspaceFolderCapability = false;

const INSTRUCTIONS = [
    'CMP', 'CALL_EQ', 'CALL_NEQ', 'JP_NEQ', 'CALL_LS', 'CALL_LT', 'CALL_GT',
    'JP_EQ', 'JP_LS', 'JP_LT', 'JP_GT', 'NOP', 'HALT', 'MOV', 'LDI', 'STR',
    'ADD', 'SUB', 'MUL', 'DIV', 'SHL', 'SHR', 'NOT', 'AND', 'NAND', 'OR', 'XOR',
    'JP', 'JPC', 'JPZ', 'CALL', 'RTS', 'PUSH', 'POP', 'GET_SP', 'SET_SP',
    'GET_PC', 'SET_IVR', 'INT', 'RTI', 'GET_INT_ID'
];

const LABEL_INSTRUCTIONS = new Set([
    'SET_IVR', 'SET_SP', 'GET_PC', 'GET_SP',
    'JP', 'JPZ', 'JPC',
    'CALL', 'CALL_EQ', 'CALL_NEQ', 'CALL_LT', 'CALL_GT',
    'JP_EQ', 'JP_NEQ', 'JP_LT', 'JP_GT'
]);

const DIRECTIVES = ['!IMPORT', '!DECLARE', '!DEFINE'];

connection.onInitialize((params: InitializeParams) => {
    connection.console.log('DASM Language Server initializing...');
    const capabilities = params.capabilities;

    hasConfigurationCapability = !!(
        capabilities.workspace && !!capabilities.workspace.configuration
    );
    hasWorkspaceFolderCapability = !!(
        capabilities.workspace && !!capabilities.workspace.workspaceFolders
    );

    const result: InitializeResult = {
        capabilities: {
            textDocumentSync: TextDocumentSyncKind.Incremental,
            completionProvider: {
                resolveProvider: true,
                triggerCharacters: ['.', '@', '!']
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

    return result;
});

connection.onInitialized(() => {
    if (hasConfigurationCapability) {
        connection.client.register(DidChangeConfigurationNotification.type, undefined);
    }
    if (hasWorkspaceFolderCapability) {
        connection.workspace.onDidChangeWorkspaceFolders(() => {
            connection.console.log('Workspace folder change event received.');
        });
    }

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
            if (entry.name === 'node_modules' || entry.name.startsWith('.')) continue;
            scanWorkspaceFiles(fullPath);
        } else if (entry.isFile() && (entry.name.endsWith('.asm') || entry.name.endsWith('.dasm'))) {
            try {
                const content = fs.readFileSync(fullPath, 'utf8');
                const uri = pathToFileURL(fullPath).toString();
                parseDocument(content, uri);
            } catch {
                // ignore unreadable files
            }
        }
    }
}

interface RegisterAnnotation {
    register: string;
    description: string;
}

interface LabelInfo {
    name: string;
    namespace: string;
    document: string;
    line: number;
    registers: RegisterAnnotation[];
    description?: string;
    returns?: string;
    deprecated?: string | true;
    wip?: string | true;
}

interface DefineInfo {
    name: string;
    value: string;
    document: string;
}

let labelStore: LabelInfo[] = [];
let defineStore: DefineInfo[] = [];
const importsByDoc: Map<string, Map<string, string>> = new Map();

function namespaceForDoc(documentUri: string): string {
    try {
        const filePath = fileURLToPath(documentUri);
        return path.basename(filePath).replace(/\.(asm|dasm)$/i, '');
    } catch {
        return '';
    }
}

function parseImports(text: string, docUri: string): void {
    const lines = text.split('\n');
    const aliases = new Map<string, string>();
    const importRe = /^\s*!\s*(?:IMPORT|import)\s+["']?([^"'\s]+)["']?(?:\s+(?:as|AS)\s+(\S+))?/;
    for (const raw of lines) {
        const m = raw.match(importRe);
        if (!m) continue;
        const filePath = m[1];
        const alias = m[2];
        const base = path.basename(filePath).replace(/\.(asm|dasm)$/i, '');
        const key = alias || base;
        aliases.set(key, base);
    }
    importsByDoc.set(docUri, aliases);
}

// !DECLARE Name = value  (assembler-native)
// !DEFINE  Name = value  (extension alias — same semantics)
function parseDefines(text: string, docUri: string): void {
    defineStore = defineStore.filter(d => d.document !== docUri);
    const defineRe = /^\s*!\s*(?:DECLARE|declare|DEFINE|define)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)/;
    for (const raw of text.split('\n')) {
        const m = raw.match(defineRe);
        if (!m) continue;
        defineStore.push({ name: m[1].trim(), value: m[2].trim(), document: docUri });
    }
}

function parseDocument(text: string, documentUri: string): void {
    parseImports(text, documentUri);
    parseDefines(text, documentUri);
    const namespace = namespaceForDoc(documentUri);
    const lines = text.split('\n');

    labelStore = labelStore.filter(l => l.document !== documentUri);

    let pendingRegisters: RegisterAnnotation[] = [];
    let pendingDescription: string | undefined;
    let pendingReturns: string | undefined;
    let pendingDeprecated: string | true | undefined;
    let pendingWip: string | true | undefined;

    const resetPending = () => {
        pendingRegisters = [];
        pendingDescription = undefined;
        pendingReturns = undefined;
        pendingDeprecated = undefined;
        pendingWip = undefined;
    };

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();

        if (line.length === 0 || line.startsWith(';')) {
            continue;
        }

        // Register annotation: @REA: desc | @REA desc | @REA
        // Restricted to RE[A-Z] so we don't shadow @desc / @wip / etc.
        const registerMatch = line.match(/^@(RE[A-Z])\b\s*[:\s]?\s*(.*)$/);
        if (registerMatch) {
            pendingRegisters.push({
                register: registerMatch[1],
                description: registerMatch[2].trim()
            });
            continue;
        }

        const annotationMatch = line.match(/^@([a-zA-Z]+)\b\s*:?\s*(.*)$/);
        if (annotationMatch) {
            const tag = annotationMatch[1].toLowerCase();
            const rest = annotationMatch[2].trim();
            switch (tag) {
                case 'description':
                case 'desc':
                    pendingDescription = rest;
                    break;
                case 'returns':
                case 'return': {
                    pendingReturns = rest;
                    break;
                }
                case 'deprecated':
                    pendingDeprecated = rest.length > 0 ? rest : true;
                    break;
                case 'wip':
                    pendingWip = rest.length > 0 ? rest : true;
                    break;
                default:
                    // unknown annotation: ignore but still treat as pending so it doesn't reset the block
                    break;
            }
            continue;
        }

        const labelMatch = line.match(/^([a-zA-Z_][a-zA-Z0-9_.]*):/);
        if (labelMatch) {
            const labelName = labelMatch[1];
            labelStore.push({
                name: labelName,
                namespace,
                document: documentUri,
                line: i,
                registers: [...pendingRegisters],
                description: pendingDescription,
                returns: pendingReturns,
                deprecated: pendingDeprecated,
                wip: pendingWip
            });
            resetPending();
            continue;
        }

        // Any other non-empty, non-comment line resets the annotation block.
        resetPending();
    }
}

documents.onDidChangeContent((change) => {
    parseDocument(change.document.getText(), change.document.uri);
    revalidateAllOpen();
});

documents.onDidOpen((event) => {
    parseDocument(event.document.getText(), event.document.uri);
    revalidateAllOpen();
});

documents.onDidClose((event) => {
    // Clear diagnostics for closed documents so stale warnings don't linger.
    connection.sendDiagnostics({ uri: event.document.uri, diagnostics: [] });
});

function revalidateAllOpen(): void {
    for (const doc of documents.all()) {
        validateDeprecatedRefs(doc);
    }
}

// Pick up files created/changed/deleted on disk that are not currently open
// in an editor (the client forwards these via workspace/didChangeWatchedFiles).
connection.onDidChangeWatchedFiles((params) => {
    for (const change of params.changes) {
        if (change.type === 3 /* Deleted */) {
            labelStore = labelStore.filter(l => l.document !== change.uri);
            defineStore = defineStore.filter(d => d.document !== change.uri);
            importsByDoc.delete(change.uri);
            continue;
        }
        // Skip if the document is already managed by the open-document store —
        // that path stays authoritative and we'd just double-parse.
        if (documents.get(change.uri)) continue;
        try {
            const fsPath = fileURLToPath(change.uri);
            const content = fs.readFileSync(fsPath, 'utf8');
            parseDocument(content, change.uri);
        } catch {
            // ignore unreadable files
        }
    }
    revalidateAllOpen();
});

function namespaceCandidates(prefix: string, contextDocUri: string): string[] {
    const out: string[] = [];
    const seen = new Set<string>();
    const add = (ns: string | undefined) => {
        if (!ns) return;
        const k = ns.toLowerCase();
        if (seen.has(k)) return;
        seen.add(k);
        out.push(ns);
    };
    add(importsByDoc.get(contextDocUri)?.get(prefix));
    add(prefix);
    return out;
}

function resolveLabel(word: string, contextDocUri: string): LabelInfo | undefined {
    if (word.includes('.')) {
        const dot = word.lastIndexOf('.');
        const prefix = word.substring(0, dot);
        const name = word.substring(dot + 1);
        const candidates = namespaceCandidates(prefix, contextDocUri).map(c => c.toLowerCase());

        for (const ns of candidates) {
            const m = labelStore.find(l => l.namespace.toLowerCase() === ns && l.name === name);
            if (m) return m;
        }
        for (const ns of candidates) {
            const m = labelStore.find(l =>
                l.namespace.toLowerCase() === ns && l.name.toLowerCase() === name.toLowerCase()
            );
            if (m) return m;
        }
        return labelStore.find(l => l.name === name)
            ?? labelStore.find(l => l.name.toLowerCase() === name.toLowerCase());
    }

    const inDoc = labelStore.find(l => l.document === contextDocUri && l.name === word);
    if (inDoc) return inDoc;
    return labelStore.find(l => l.name === word);
}

function hasAnyAnnotation(info: LabelInfo): boolean {
    return info.registers.length > 0
        || !!info.description
        || !!info.returns
        || info.deprecated !== undefined
        || info.wip !== undefined;
}

function renderLabelMarkdown(info: LabelInfo): string {
    const title = info.namespace ? `${info.namespace}.${info.name}` : info.name;
    let md = `**${title}**\n\n`;

    if (info.deprecated !== undefined) {
        const reason = typeof info.deprecated === 'string' ? `: ${info.deprecated}` : '';
        md += `> ⚠ **Deprecated**${reason}\n\n`;
    }
    if (info.wip !== undefined) {
        const reason = typeof info.wip === 'string' ? `: ${info.wip}` : '';
        md += `> 🚧 **Work in progress**${reason}\n\n`;
    }
    if (info.description) {
        md += `${info.description}\n\n`;
    }
    if (info.registers.length > 0) {
        md += `**Parameters**\n\n`;
        for (const reg of info.registers) {
            md += `- **${reg.register}**: ${reg.description}\n`;
        }
        md += `\n`;
    }
    if (info.returns) {
        md += `**Returns**: ${info.returns}\n`;
    }
    return md.trimEnd();
}

// Scan a document and emit warning diagnostics (with strikethrough) for
// any reference to a deprecated label.
function validateDeprecatedRefs(document: TextDocument): void {
    const uri = document.uri;
    const lines = document.getText().split('\n');
    const diagnostics: Diagnostic[] = [];
    const wordRe = /\b([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)\b/g;

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmed = line.trimStart();
        // Skip annotation lines, comments, and label definitions — only
        // scan actual instruction/operand lines for references.
        if (trimmed.startsWith('@') || trimmed.startsWith(';')) continue;

        wordRe.lastIndex = 0;
        let match: RegExpExecArray | null;
        while ((match = wordRe.exec(line)) !== null) {
            const word = match[1];
            const info = resolveLabel(word, uri);
            if (!info || info.deprecated === undefined) continue;

            const reason = typeof info.deprecated === 'string'
                ? `: ${info.deprecated}`
                : '';

            diagnostics.push({
                range: {
                    start: { line: i, character: match.index },
                    end: { line: i, character: match.index + word.length }
                },
                severity: DiagnosticSeverity.Warning,
                tags: [DiagnosticTag.Deprecated],
                message: `'${info.name}' is deprecated${reason}`,
                source: 'dasm'
            });
        }
    }

    connection.sendDiagnostics({ uri, diagnostics });
}

connection.onHover((textDocumentPosition: TextDocumentPositionParams): Hover | undefined => {
    const document = documents.get(textDocumentPosition.textDocument.uri);
    if (!document) return undefined;

    const text = document.getText();
    const lines = text.split('\n');
    const line = lines[textDocumentPosition.position.line];
    if (!line) return undefined;

    const position = textDocumentPosition.position;
    let start = position.character;
    let end = position.character;

    while (start > 0 && /[a-zA-Z0-9_.]/.test(line[start - 1])) start--;
    while (end < line.length && /[a-zA-Z0-9_.]/.test(line[end])) end++;

    const word = line.substring(start, end);
    if (!word) return undefined;

    const info = resolveLabel(word, textDocumentPosition.textDocument.uri);
    if (!info || !hasAnyAnnotation(info)) return undefined;

    return {
        contents: {
            kind: MarkupKind.Markdown,
            value: renderLabelMarkdown(info)
        }
    };
});

function getPrefixContext(line: string, character: number): {
    leading: string;
    word: string;
    afterDot: { ns: string } | null;
    afterInstruction: string | null;
} {
    const upTo = line.slice(0, character);
    const leading = upTo.match(/^\s*/)?.[0] ?? '';

    let wStart = character;
    while (wStart > 0 && /[a-zA-Z0-9_.!]/.test(upTo[wStart - 1])) wStart--;
    const word = upTo.slice(wStart);

    let afterDot: { ns: string } | null = null;
    if (word.includes('.')) {
        const dot = word.lastIndexOf('.');
        afterDot = { ns: word.substring(0, dot) };
    }

    let afterInstruction: string | null = null;
    const beforeWord = upTo.slice(0, wStart).trimEnd();
    const instMatch = beforeWord.match(/(?:^|\s)([A-Z_]+)$/);
    if (instMatch && LABEL_INSTRUCTIONS.has(instMatch[1])) {
        afterInstruction = instMatch[1];
    }

    return { leading, word, afterDot, afterInstruction };
}

connection.onCompletion(
    (params: TextDocumentPositionParams): CompletionItem[] => {
        const document = documents.get(params.textDocument.uri);
        if (!document) return [];

        const text = document.getText();
        const lines = text.split('\n');
        const line = lines[params.position.line] ?? '';
        const ctx = getPrefixContext(line, params.position.character);

        // Mode 1: namespace-qualified -> labels in that namespace only
        if (ctx.afterDot) {
            const candidates = new Set(
                namespaceCandidates(ctx.afterDot.ns, params.textDocument.uri).map(c => c.toLowerCase())
            );
            const items: CompletionItem[] = [];
            const seen = new Set<string>();
            for (const info of labelStore) {
                if (!candidates.has(info.namespace.toLowerCase())) continue;
                if (seen.has(info.name)) continue;
                seen.add(info.name);
                items.push({
                    label: info.name,
                    kind: CompletionItemKind.Function,
                    detail: `${info.namespace}.${info.name}`,
                    documentation: hasAnyAnnotation(info)
                        ? { kind: MarkupKind.Markdown, value: renderLabelMarkdown(info) }
                        : undefined
                });
            }
            return items;
        }

        // Mode 2: after a label-taking instruction -> import aliases + namespace bases + current-doc labels
        if (ctx.afterInstruction) {
            const items: CompletionItem[] = [];
            const seenNs = new Set<string>();

            // Explicit import aliases from this document first — they may not yet
            // have any labels in the store if the imported file wasn't scanned.
            const aliasMap = importsByDoc.get(params.textDocument.uri);
            if (aliasMap) {
                for (const [alias] of aliasMap) {
                    if (seenNs.has(alias)) continue;
                    seenNs.add(alias);
                    items.push({
                        label: alias,
                        kind: CompletionItemKind.Module,
                        detail: `import alias (${alias})`
                    });
                }
            }

            // Namespace bases derived from all known labels
            for (const info of labelStore) {
                if (!info.namespace || seenNs.has(info.namespace)) continue;
                seenNs.add(info.namespace);
                items.push({
                    label: info.namespace,
                    kind: CompletionItemKind.Module,
                    detail: `namespace (${info.namespace})`
                });
            }

            // Current-doc labels
            for (const info of labelStore) {
                if (info.document !== params.textDocument.uri) continue;
                items.push({
                    label: info.name,
                    kind: CompletionItemKind.Function,
                    detail: info.namespace ? `${info.namespace}.${info.name}` : info.name,
                    documentation: hasAnyAnnotation(info)
                        ? { kind: MarkupKind.Markdown, value: renderLabelMarkdown(info) }
                        : undefined
                });
            }
            return items;
        }

        // Mode 3: bare line / start-of-token -> instructions + directives + defines + import aliases
        const items: CompletionItem[] = [];
        for (const inst of INSTRUCTIONS) {
            items.push({ label: inst, kind: CompletionItemKind.Keyword, detail: 'instruction' });
        }
        for (const dir of DIRECTIVES) {
            items.push({ label: dir, kind: CompletionItemKind.Keyword, detail: 'directive' });
        }

        // !DECLARE / !DEFINE constants (all files — they may be used cross-file via imports)
        const seenDef = new Set<string>();
        for (const def of defineStore) {
            if (seenDef.has(def.name)) continue;
            seenDef.add(def.name);
            items.push({
                label: def.name,
                kind: CompletionItemKind.Variable,
                detail: `= ${def.value}`,
                documentation: `Defined in ${path.basename(fileURLToPath(def.document))}`
            });
        }

        // Import aliases from the current document
        const currentAliases = importsByDoc.get(params.textDocument.uri);
        if (currentAliases) {
            for (const [alias] of currentAliases) {
                items.push({
                    label: alias,
                    kind: CompletionItemKind.Module,
                    detail: `import alias (${alias})`
                });
            }
        }

        return items;
    }
);

connection.onCompletionResolve((item: CompletionItem): CompletionItem => item);

documents.listen(connection);
connection.listen();
