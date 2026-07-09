# Python Project Inspector

Analyze Git history metrics for Python/Odoo projects.

## Install

```bash
uv sync
```

## Commands

Global options (`--repo`, `--branch`, …) go **before** the subcommand:

```bash
uv run ppi \
  --repo /path/to/repo --branch dev \
  doctor

uv run ppi \
  --repo /path/to/repo --branch dev \
  analyze --all-modules

uv run ppi \
  --repo /path/to/repo --branch dev \
  doctor --recover-stale

uv run ppi \
  --repo /path/to/repo --branch dev \
  serve --open
```

## Dashboard frontend

Build the React/Mantine UI before `serve` (the server prefers `frontend/dist` when present):

```bash
cd frontend
npm install
npm run build
```

Dashboard tabs: **Report** (commit-scoped entity graph, file treemap with drilldown, metric chips), **Dashboard** (entity kind + metric + aggregation selector, timeseries and hotspots), **Tables** (modules, files, relations, drilldown stack).

The frontend consumes only the typed `/api/v1` contract; see
[`frontend/MIGRATION.md`](frontend/MIGRATION.md) for the migration
ledger.

Snapshot query examples:

```bash
uv run ppi --repo /path/to/repo query --metric modules --format json
uv run ppi --repo /path/to/repo query --metric graph --format json
uv run ppi --repo /path/to/repo query --metric edge-points --source mod_a --target mod_b --format json
uv run ppi --repo /path/to/repo query --metric failures --format json
```

For local UI development with API proxy:

```bash
uv run ppi --repo /path/to/repo --branch dev serve --port 8765
cd frontend && npm run dev
```

The DuckDB history store lives in `<repo>/.ppi/history.duckdb` (git-ignored). Worktree, lock files, and runtime metadata stay under `~/.local/share/ppi/` (or `--analysis-dir`).

## VS Code extension

A thin bridge extension lets you analyze a workspace and view the dashboard
inside VS Code (Stage 5). It spawns the `ppi` CLI (`analyze --json` for progress;
`rpc` for the read-only dashboard data) and hosts the existing React dashboard in
a Webview — no HTTP server is started for the panel.

Build the webview bundle and the extension:

```bash
cd frontend && npm install && npm run build:webview   # -> vscode-extension/dist-webview
cd ../vscode-extension && npm install && npm run build  # -> dist/extension.js
```

Package and install locally:

```bash
cd vscode-extension && npm run package   # -> ppi-vscode-0.1.0.vsix
code --install-extension ./ppi-vscode-0.1.0.vsix
```

Commands: `PPI: Analyze Project`, `PPI: Analyze Project (Rebuild)`, `PPI: Open
Dashboard`, `PPI: Cancel Analysis`. Settings: `ppi.profile`, `ppi.analysisDir`,
`ppi.pythonExecutable`, `ppi.cliPath` (workspace-over-global precedence).

## Worker IPC boundary (new)

PPI now supports a dedicated workspace worker for each registered project.
The worker owns analysis execution, queries, progress events, and storage writes.
CLI, FastAPI/web UI, and VS Code communicate through one shared command/event boundary.

```bash
uv run ppi --repo /path/to/repo worker start            # start a workspace worker
uv run ppi --repo /path/to/repo worker status            # check worker health
uv run ppi --repo /path/to/repo worker stop              # stop the worker
uv run ppi --repo /path/to/repo analyze --via-worker     # analyze through worker
uv run ppi --repo /path/to/repo query --via-worker --metric snapshot-table-modules --format json  # query through worker
```

The worker uses Unix domain sockets and `msgspec` MessagePack framing.
Protocol version is `1.0`. Runtime metadata lives under `$XDG_RUNTIME_DIR/ppi`
or `/tmp/ppi/<uid>/<workspace_id>/`.

Existing direct CLI flows remain available:
- `ppi analyze --json` (direct, no worker)
- `ppi rpc` (legacy stdio JSON-RPC — still works but is superseded by the worker IPC boundary)

Protocol contract: `contracts/protocol.md`.

Machine-readable progress stream and read-only query surface:

```bash
uv run ppi --repo /path/to/repo analyze --json          # JSON-lines progress events
uv run ppi --repo /path/to/repo rpc                      # legacy stdio JSON-RPC query servant
```

## API contract workflow

PPI ships a single source of truth for the HTTP contract: the
OpenAPI schema exported from the FastAPI app, linted by Spectral and
Redocly, bundled, and used to generate the typed `openapi-fetch`
client for the React dashboard.

```bash
make api-contract        # export + lint + bundle + generate TS types
make api-freshness       # regenerated artifacts must match what is committed
make api-boundaries      # scanner self-test + boundary check
make api-diff            # diff exported OpenAPI against the frozen baseline
```

`openapi/openapi.baseline.json` is the first stable
`/api/v1` snapshot; non-additive changes require a deliberate
`make api-bump-baseline` and a migration note in
`frontend/MIGRATION.md`.

Legacy `/api/<method>` RPC endpoints are still available
(`ppi rpc` and the webview envelope decoder) but new generic
frontend code goes through the typed `/api/v1` facade only.
