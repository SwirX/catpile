# Tools: VSCode Extension

Build a VSCode extension for CatLang syntax highlighting and LSP integration.

## Extension Structure

Two extensions are available:

- **`vscode-catpile/`** - Lightweight (syntax highlighting only)
- **`catpile-vscode/`** - Full (syntax highlighting + LSP client)

## Lightweight Extension

### `syntaxes/catlang.tmLanguage.json`

```json
{
  "scopeName": "source.cat",
  "fileTypes": ["cat"],
  "patterns": [
    {"include": "#comments"},
    {"include": "#strings"},
    {"include": "#keywords"},
    {"include": "#scope-vars"},
    {"include": "#actions"}
  ],
  "repository": {
    "comments": {
      "patterns": [{"match": "#.*$", "name": "comment.line.number-sign.cat"}]
    },
    "strings": {
      "patterns": [{"match": "\"[^\"]*\"", "name": "string.quoted.double.cat"}]
    },
    "keywords": {
      "match": "\\b(on|fn|if|else|repeat|repeat_forever|foreach|break|return|script)\\b",
      "name": "keyword.control.cat"
    },
    "scope-vars": {
      "match": "\\b[log]_[a-zA-Z_][a-zA-Z0-9_]*\\b",
      "name": "variable.other.scoped.cat"
    },
    "actions": {
      "match": "\\b(log|show|hide|set|wait|inc|dec|mul|div)\\b",
      "name": "support.function.cat"
    }
  }
}
```

### `package.json`

```json
{
  "name": "vscode-catpile",
  "displayName": "CatLang",
  "contributes": {
    "languages": [{
      "id": "cat",
      "aliases": ["CatLang", "cat"],
      "extensions": [".cat"],
      "configuration": "./language-configuration.json"
    }],
    "grammars": [{
      "language": "cat",
      "scopeName": "source.cat",
      "path": "./syntaxes/catlang.tmLanguage.json"
    }]
  }
}
```

### `language-configuration.json`

```json
{
  "comments": {"lineComment": "#"},
  "brackets": [["(", ")"], ["{", "}"]],
  "autoClosingPairs": [
    {"open": "(", "close": ")"},
    {"open": "\"", "close": "\""}
  ]
}
```

## Full Extension (with LSP)

### LSP Server

The LSP server in `catpile/lsp.py` provides:
- **Completion** - action names, variable names, page paths
- **Hover** - action documentation
- **Diagnostics** - syntax errors
- **Definition** - go to function definition
- **References** - find variable usages

### LSP Client (VSCode)

```typescript
// extension.ts
import * as vscode from 'vscode';
import { LanguageClient, ServerOptions, TransportKind } from 'vscode-languageclient';

export function activate(context: vscode.ExtensionContext) {
  const serverOptions: ServerOptions = {
    command: 'python3',
    args: ['-m', 'catpile.lsp'],
    transport: TransportKind.stdio
  };

  const client = new LanguageClient('catpile', 'CatLang LSP', serverOptions, {
    documentSelector: [{ scheme: 'file', language: 'cat' }]
  });

  context.subscriptions.push(client.start());
}
```

### Features Provided

| Feature | Implementation |
|---|---|
| Syntax highlighting | TextMate grammar (`.tmLanguage.json`) |
| Auto-complete | LSP `textDocument/completion` |
| Error squiggles | LSP `textDocument/publishDiagnostics` |
| Hover docs | LSP `textDocument/hover` |
| Go to definition | LSP `textDocument/definition` |
| Find references | LSP `textDocument/references` |
| Formatting | LSP `textDocument/formatting` |
| Color preview | LSP `textDocument/documentColor` |
