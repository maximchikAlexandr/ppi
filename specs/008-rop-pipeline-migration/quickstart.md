# Quickstart: Validate ROP Pipeline Migration

**Spec ID**: `008-rop-pipeline-migration`  
**Date**: 2026-07-04

This quickstart describes validation scenarios for the refactor. Exact commands may be adjusted to the repository's current scripts, but these are the expected validation classes.

## Anti-Cosmetic Migration Rule

A covered process is **not** migrated if only a top-level `pipe(...)` invocation wraps an unchanged imperative block. Completion requires:

1. Named stages with typed success/failure contracts.
2. Independently testable stage functions.
3. Explicit effect/framework/compatibility adapters at boundaries.
4. Characterization tests proving behavior preservation.

Remaining imperative/object shells must be inventoried with adapter names, target paths, and justifications.

## Repository Path Guardrails

Before implementing any task, verify target paths against the current layout:

- **Python core**: use `src/ppi/core/pipelines/` — do not create `src/ppi/analysis`.
- **Frontend**: use `frontend/src/api`, `frontend/src/transforms`, `frontend/src/pages`, `frontend/src/components` — do not create `frontend/src/features`.
- **VS Code**: use existing `vscode-extension/src/` — inventory records exact files before edits.

Any reorganization must be recorded in the migration inventory (`handoff/implementation-decisions.md`) before code movement starts.

## Prerequisites

- Python environment synced with project dependencies.
- Frontend dependencies installed.
- VS Code extension dependencies installed when validating bridge slices.
- A representative fixture repository or sample Odoo/Python project for characterization.

## Repository Path Sanity Check

Before implementing any task, inspect the current repository layout and record exact entrypoint files in `specs/008-rop-pipeline-migration/handoff/implementation-decisions.md`:

```bash
find src/ppi -maxdepth 2 -type d | sort
find frontend/src -maxdepth 2 -type d | sort
find vscode-extension/src -maxdepth 2 -type d | sort
```

Expected outcome:

- Python core work targets `src/ppi/core` and `src/ppi/history`, not a newly invented `src/ppi/analysis` tree.
- Frontend read/view-model work targets `frontend/src/api`, `frontend/src/transforms`, `frontend/src/pages`, and `frontend/src/components`, not a newly invented `frontend/src/features` tree.
- Any repository reorganization is documented in the migration inventory before code movement starts.

## Baseline Capture

Before migrating each slice:

```bash
uv sync
uv run ppi --repo /path/to/repo --branch dev analyze --all-modules
uv run ppi --repo /path/to/repo query --metric modules --format json > before-modules.json
uv run ppi --repo /path/to/repo query --metric graph --format json > before-graph.json
uv run ppi --repo /path/to/repo query --metric failures --format json > before-failures.json
```

Expected outcome:

- Baseline commands succeed for a valid fixture.
- Baseline JSON files are saved for semantic comparison.

## Python Core Validation

After Slice 1 and Slice 2:

```bash
uv run pytest
uv run ppi --repo /path/to/repo --branch dev analyze --all-modules
uv run ppi --repo /path/to/repo query --metric modules --format json > after-modules.json
uv run ppi --repo /path/to/repo query --metric graph --format json > after-graph.json
uv run ppi --repo /path/to/repo query --metric failures --format json > after-failures.json
```

Expected outcome:

- Tests pass.
- Valid analysis output is semantically equivalent to baseline.
- Invalid addons path test returns typed validation failure.
- Malformed manifest or parse failure remains recoverable report data when applicable.

## Python History/Effect Validation

After Slice 3:

```bash
uv run pytest
uv run ppi --repo /path/to/repo --branch dev analyze --json
```

Expected outcome:

- Progress events still stream in the expected shape.
- Git/worktree failures are typed orchestration failures.
- Cancellation/partial history behavior matches existing product behavior or documented semantics.

## TypeScript Frontend Validation

After Slice 4 and Slice 5:

```bash
cd frontend
npm install
npm run build
npm test -- --run
```

Expected outcome:

- Build succeeds.
- API/RPC read pipeline tests distinguish transport, schema, and mapping failures.
- Dashboard and graph components render supplied view models and typed errors.
- Core view-model derivation is testable without mounting React components.

## VS Code Bridge Validation

After Slice 6:

```bash
cd frontend && npm run build:webview
cd ../vscode-extension
npm install
npm run build
npm run package
```

Expected outcome:

- Extension build/package succeeds.
- Bridge tests cover settings resolution, CLI spawn failure, malformed progress event, RPC startup failure, cancellation, and webview handoff.
- Existing commands remain available: analyze project, rebuild, open dashboard, cancel analysis.

## Cleanup Validation

After Slice 7:

- Migration inventory has no unreviewed compatibility adapters.
- Deprecated pipe helpers are removed or isolated.
- Remaining framework/effect shells are listed with adapter names and justifications.
- Stage-contract tests cover at least the target coverage threshold.
- No covered primary process is only a top-level pipe wrapper around old imperative internals.
