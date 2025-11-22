import * as vscode from 'vscode';
import * as path from 'path';
import { LanguageClient, LanguageClientOptions, ServerOptions, TransportKind } from 'vscode-languageclient/node';

let client: LanguageClient;

export function activate(context: vscode.ExtensionContext) {
    console.log('DASM extension activating...');
    
    // The server is implemented in node
    const serverModule = context.asAbsolutePath(path.join('out', 'server.js'));
    
    console.log('Server module path:', serverModule);
    
    // The debug options for the server
    // --inspect=6009: runs the server in Node's Inspector mode so VS Code can attach to the server for debugging
    const debugOptions = { execArgv: ['--nolazy', '--inspect=6009'] };

    // If the extension is launched in debug mode then the debug server options are used
    // Otherwise the run options are used
    const serverOptions: ServerOptions = {
        run: { module: serverModule, transport: TransportKind.ipc },
        debug: {
            module: serverModule,
            transport: TransportKind.ipc,
            options: debugOptions
        }
    };

    // Options to control the language client
    const clientOptions: LanguageClientOptions = {
        // Register the server for dasm documents
        documentSelector: [
            { scheme: 'file', language: 'dasm' },
            { scheme: 'file', pattern: '**/*.asm' },
            { scheme: 'file', pattern: '**/*.dasm' }
        ],
        synchronize: {
            // Notify the server about file changes to '.asm' and '.dasm' files contained in the workspace
            fileEvents: vscode.workspace.createFileSystemWatcher('**/*.{asm,dasm}')
        }
    };

    // Create the language client and start the client.
    client = new LanguageClient(
        'dasmLanguageServer',
        'DASM Language Server',
        serverOptions,
        clientOptions
    );

    console.log('Starting language client...');

    // Start the client. This will also launch the server
    client.start().then(() => {
        console.log('DASM language server started successfully');
    }).catch((error) => {
        console.error('Failed to start DASM language server:', error);
    });
}

export function deactivate(): Thenable<void> | undefined {
    if (!client) {
        return undefined;
    }
    return client.stop();
}