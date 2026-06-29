# Python Project Inspector for VS Code

Thin bridge that runs the `ppi` CLI from inside VS Code and renders the existing
dashboard in a Webview panel.

## Build

```sh
npm install
npm run build      # bundles the extension host to dist/extension.js
npm run build:webview   # builds the dashboard webview bundle (cd ../frontend && npm run build:webview)
```

`npm run package` and `npm run vscode:prepublish` build both the extension host
and the webview bundle automatically, so packaging never ships a panel without a
dashboard.

## Package & install locally

```sh
npm run package    # produces ppi-vscode-0.1.0.vsix
code --install-extension ./ppi-vscode-0.1.0.vsix
```

After installation, open a workspace folder and look for the **PPI** icon in the
Activity Bar (left side). Clicking it opens the PPI sidebar with quick actions:
Analyze Project, Analyze Project (Rebuild), Open Dashboard, Cancel Analysis,
Open Settings. The same commands are also available in the Command Palette
under `PPI:` and in the Explorer context menu / editor title bar.

## Commands

- `PPI: Analyze Project` — runs `ppi analyze --json` and shows live progress.
- `PPI: Analyze Project (Rebuild)` — same, forcing a full rebuild.
- `PPI: Open Dashboard` — opens the dashboard in a Webview panel.
- `PPI: Cancel Analysis` — terminates the running analysis.
- `PPI: Open Settings` — opens the PPI settings section.

## Settings

- `ppi.profile` — `odoo` (default; `python` is reserved until CLI support lands).
- `ppi.analysisDir` — custom analysis/results directory.
- `ppi.pythonExecutable` — interpreter to run `ppi` as `<exe> -m ppi`.
- `ppi.cliPath` — explicit path to the `ppi` console script.
