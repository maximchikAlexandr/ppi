# Migration Inventory: Railway Oriented Pipeline Migration

**Spec**: `specs/008-rop-pipeline-migration/spec.md`
**Last Updated**: 2026-07-04

## Repository Path Grounding

Discovered entrypoint files from current repository layout:

### Python Backend

| Pipeline | Current Entry Point | Target Path Family | Target Stages | Remaining Shells | Compatibility Adapters | Required Tests | Status |
|---|---|---|---|---|---|---|---|
| `odoo_project_analysis_pipeline` | `src/ppi/core/analyzer.py:run_odoo_pipeline` | `src/ppi/core/pipelines/` | config, addons validation, discovery, enrichment, provider index, edge detection, freeze/export | filesystem scan/read via `src/ppi/adapters/filesystem` | `src/ppi/core/compat.py` — tombstone (removed) | valid output, invalid addons, malformed manifest, edge/provider consistency | migrated |
| `module_enrichment_pipeline` | `src/ppi/core/odoo/pipeline.py:enrich_modules_with_code_analysis` | `src/ppi/core/pipelines/` | metrics, complexity, AST facts, model expression resolution | AST visitor shell, file read adapter | `src/ppi/core/compat.py` — tombstone (removed) | parse failure, unsupported model expr, metrics/complexity success | migrated |
| `history_walk_analysis_pipeline` | `src/ppi/history/walker.py` (module-level entry) | `src/ppi/history/pipelines/` | commit ingestion, plan, worktree prepare, per-commit checkout/analyze/persist | Git, worktree, filesystem, progress, persistence | none | invalid repo, checkout failure, partial history behavior | migrated |

### Frontend

| Pipeline | Current Entry Point | Target Path Family | Target Stages | Remaining Shells | Compatibility Adapters | Required Tests | Status |
|---|---|---|---|---|---|---|---|
| `frontend_api_read_pipeline` | `frontend/src/api/client.ts` (main API client) | `frontend/src/api/` | request, transport, decode, DTO/domain map, UI error map | transport/RPC | none (native typed fetch functions) | transport error, schema error, valid response | migrated |
| `frontend_dashboard_viewmodel_pipeline` | `frontend/src/pages/Dashboard.tsx` (render shell) | `frontend/src/transforms/` + `frontend/src/pages/` | normalize, metrics, aggregates, rows, treemap, timelapse, formatting | React render shell | none | valid snapshot, empty/partial data | migrated |
| `frontend_graph_view_pipeline` | `frontend/src/pages/GraphView.tsx` (render shell) | `frontend/src/transforms/` + `frontend/src/pages/` | normalize graph, labels, filter/sort, detail rows, viewport | React render shell | none | visible edge filters, empty graph, invalid data | migrated |

### VS Code Bridge

| Pipeline | Current Entry Point | Target Path Family | Target Stages | Remaining Shells | Compatibility Adapters | Required Tests | Status |
|---|---|---|---|---|---|---|---|
| `vscode_analysis_bridge_pipeline` | `vscode-extension/src/extension.ts` (command handlers) | `vscode-extension/src/bridge/` + `vscode-extension/src/rop/` | settings, command build, spawn, progress decode, RPC start, webview handoff | VS Code APIs, process, webview | none | spawn failure, malformed progress, cancellation | migrated |

## Anti-Cosmetic Completion Contract

- No covered pipeline may be marked `migrated` if only a top-level `pipe(...)` wraps unchanged imperative internals.
- Each named stage must be independently testable with typed success/failure contracts.
- Remaining effect/framework shells must be inventoried with adapter names and justifications.
- Compatibility adapters must be removed or explicitly deferred before final completion.

## Remaining Shells

### Python
- **FilesystemAdapter** (`src/ppi/adapters/filesystem.py`): rglob, file reads, path checks for addons/manifests/source scans. Reason: filesystem IO is inherently effectful.
- **ASTVisitorShell** (`src/ppi/core/odoo/class_analysis.py:MethodAnalyzer`): walks Python AST using visitor pattern. Reason: the visitor is the natural framework for AST traversal; pure extraction rules live in `model_expr.py` and `ast_extract.py`.

### TypeScript
- **TransportShell** (existing `frontend/src/api/client.ts`): HTTP/fetch calls. Reason: network transport is an effect.
- **ReactRenderShell** (`frontend/src/pages/*`, `frontend/src/components/*`): component lifecycle and rendering. Reason: React is the framework boundary.

### VS Code
- **VSCodeAPIShell** (`vscode-extension/src/extension.ts`): VS Code extension lifecycle, commands, views, webview panels. Reason: VS Code API is inherently imperative/lifecycle-based.
- **ProcessShell** (spawn/kill child processes): running the CLI. Reason: subprocess management is an effect boundary.

## Cleanup Milestones

| Task | Target | Status |
|---|---|---|
| T097: Remove deprecated pipe helpers | `src/ppi/core/odoo/pipeline.py`, `src/ppi/history/` | Done — `toolz.valmap`/`curry` removed; only `toolz.pipe` remains in tests |
| T098: Remove Python compat adapters | `src/ppi/core/compat.py` | Done — tombstoned |
| T099: Remove TS compat wrappers | `frontend/src/api/client.ts`, `vscode-extension/src/bridge/` | Done — client.ts rewritten with typed fetch; bridge uses Effect |
| T108: Final inventory review | This file | Done |
| T110: Release notes | This file + `docs/development.md` | Done |
