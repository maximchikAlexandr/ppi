# Contract: VS Code extension manifest (`package.json`)

**Owner**: `vscode-extension/package.json`. **Spec ref**: FR-001, FR-005, FR-011–FR-014, FR-017, FR-025.

```jsonc
{
  "name": "ppi-vscode",
  "displayName": "Python Project Inspector",
  "publisher": "<publisher>",
  "version": "0.1.0",
  "license": "MIT",
  "repository": { "type": "git", "url": "<repo-url>" },
  "description": "Analyze Python/Odoo projects and inspect metrics from inside VS Code.",
  "icon": "media/icon.png",
  "engines": { "vscode": "^1.90.0" },
  "categories": ["Other", "Programming Languages", "Visualization"],
  "main": "./dist/extension.js",
  "activationEvents": [
    "onCommand:ppi.analyze",
    "onCommand:ppi.analyzeRebuild",
    "onCommand:ppi.openDashboard",
    "onCommand:ppi.cancelAnalysis",
    "onStartupFinished"
  ],
  "contributes": {
    "viewsContainers": {
      "activitybar": [
        { "id": "ppi", "title": "PPI", "icon": "media/icon-light.svg" }
      ]
    },
    "views": {
      "ppi": [
        { "id": "ppi.workspace", "name": "Python Project Inspector" }
      ]
    },
    "viewsWelcome": [
      {
        "view": "ppi.workspace",
        "contents": "[Analyze Project](command:ppi.analyze)\n[Analyze Project (Rebuild)](command:ppi.analyzeRebuild)\n[Open Dashboard](command:ppi.openDashboard)\n[Cancel Analysis](command:ppi.cancelAnalysis)\n[Open Settings](command:ppi.openSettings)"
      }
    ],
    "menus": {
      "explorer/context": [
        { "command": "ppi.analyze", "group": "navigation@10", "when": "explorerResourceIsFolder" },
        { "command": "ppi.openDashboard", "group": "navigation@11" }
      ],
      "editor/title": [
        { "command": "ppi.openDashboard", "group": "navigation@10" }
      ],
      "view/title": [
        { "command": "ppi.analyze", "when": "view == ppi.workspace", "group": "navigation@10" },
        { "command": "ppi.analyzeRebuild", "when": "view == ppi.workspace", "group": "navigation@11" },
        { "command": "ppi.openDashboard", "when": "view == ppi.workspace", "group": "navigation@12" },
        { "command": "ppi.cancelAnalysis", "when": "view == ppi.workspace", "group": "navigation@13" }
      ]
    },
    "commands": [
      { "command": "ppi.analyze", "title": "Analyze Project", "category": "PPI" },
      { "command": "ppi.analyzeRebuild", "title": "Analyze Project (Rebuild)", "category": "PPI" },
      { "command": "ppi.openDashboard", "title": "Open Dashboard", "category": "PPI" },
      { "command": "ppi.cancelAnalysis", "title": "Cancel Analysis", "category": "PPI" },
      { "command": "ppi.openSettings", "title": "Open Settings", "category": "PPI" }
    ],
    "configuration": {
      "title": "Python Project Inspector",
      "properties": {
        "ppi.profile": {
          "type": "string",
          "enum": ["python", "odoo"],
          "default": "odoo",
          "scope": "resource",
          "description": "Analysis profile for the workspace. NOTE: the ppi CLI currently supports `odoo`; `python` is reserved until profile support lands upstream."
        },
        "ppi.analysisDir": {
          "type": "string",
          "default": "",
          "scope": "resource",
          "description": "Custom analysis/results directory. Empty = CLI default for the repo."
        },
        "ppi.pythonExecutable": {
          "type": "string",
          "default": "",
          "scope": "machine-overridable",
          "description": "Python interpreter used to run ppi (e.g. /usr/bin/python3). If set, ppi is run as `<exe> -m ppi`."
        },
        "ppi.cliPath": {
          "type": "string",
          "default": "",
          "scope": "machine-overridable",
          "description": "Explicit path to the ppi console script. Used if ppi.pythonExecutable is empty."
        }
      }
    }
  },
  "scripts": {
    "vscode:prepublish": "node esbuild.mjs --production && npm run build:webview",
    "build": "node esbuild.mjs",
    "build:webview": "cd ../frontend && npm install && npm run build:webview",
    "package": "vsce package",
    "publish": "vsce publish",
    "test": "npm run test:unit",
    "test:unit": "node esbuild.test.mjs && node --test dist-test/*.test.js",
    "test:integration": "node ./test/runTest.js",
    "test:webview": "npm run build:webview && node esbuild.test.mjs && node --test dist-test/webview-render.test.js",
    "typecheck": "tsc --noEmit"
  },
  "devDependencies": {
    "@types/vscode": "^1.90.0",
    "@types/node": "^22.0.0",
    "esbuild": "^0.23.0",
    "@vscode/vsce": "^3.0.0",
    "@vscode/test-electron": "^2.4.0",
    "@types/vscode-webview": "^1.57.0",
    "puppeteer-core": "^23.11.1",
    "typescript": "^5.9.0"
  },
  "dependencies": {
    "zod": "^4.4.3"
  }
}
```

## Activation

`onStartupFinished` keeps the extension lazy but ready for command-palette invocation, while still letting the extension register its Activity Bar view and status-bar item on startup (so PPI is discoverable immediately after install, FR-025). The Activity Bar view (`ppi.workspace`) is the primary persistent entrypoint; the status bar only surfaces active/error run state.

## CLI resolution (`env.ts`)

1. If `ppi.pythonExecutable` set → run `["<exe>", "-m", "ppi", ...]`.
2. Else if `ppi.cliPath` set → run `["<cliPath>", ...]`.
3. Else → `["ppi", ...]` resolved from PATH.
4. If spawn fails with `ENOENT` → `CliNotFound` → error notification with an "Open Settings" action (FR-014).

## Workspace selection (`ppi.analyze`, `ppi.openDashboard`)

- Invoked from Explorer context menu with a URI → resolve the workspace folder for that URI.
- 1 folder → use it.
- N folders → QuickPick (default first); chosen folder is the analysis target (FR-017).
- 0 folders → information message, abort (FR-005).

## Packaging

`vsce package` → `ppi-vscode-0.1.0.vsix`. `.vscodeignore` excludes `src`, `test`, `node_modules`, `tsconfig.json`, `esbuild.mjs`, and the repo Python/frontend sources; includes `dist/`, `dist-webview/`, `media/`, `package.json`, `README.md`, `LICENSE`. Install locally: `code --install-extension ./ppi-vscode-0.1.0.vsix`.

## `vsce` requirements (from `microsoft/vscode-vsce`)

- `@vscode/vsce` requires Node.js >= 22.x.x.
- `vsce package`/`publish` require `LICENSE`, `README.md`, and a `repository` field in `package.json` (warns/errors otherwise). Remove `"private": true` if publishing to the Marketplace.
- Supported package managers: npm >=6 or yarn 1.x (<2). Use `--no-yarn` if needed.
- Credentials: publish via `vsce publish <PAT>` or `VSCE_PAT` env var; on Linux set `VSCE_STORE=file` to avoid `libsecret`/`keytar`.


## Webview HTML

Generated by `webviewPanel.ts` with (per the official Webview guide and `microsoft/vscode-extension-samples/webview-sample`):

- CSP via the dynamic `webview.cspSource` and a per-load nonce — NOT the deprecated literal `vscode-resource:` scheme:
  `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src ${webview.cspSource} https: data:; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}';">`
- Script tags referencing `webview.asWebviewUri(...)` for `dist-webview/assets`, each with `nonce="${nonce}"`.
- A bootstrap that calls `acquireVsCodeApi()` ONCE (guard against double-acquire) and wires `WebviewDataSource` before mounting the app.
- `localResourceRoots` restricted to the built `dist-webview` directory (and `media/` for icons) on `createWebviewPanel`.

> NOTE: `vscode-resource:` as a literal CSP source is deprecated; always use `webview.cspSource` which resolves to the correct scheme for the running VS Code version.
