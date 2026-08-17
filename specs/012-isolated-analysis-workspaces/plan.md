# Implementation Plan: Non-Blocking Branch Analysis

**Branch**: `main` | **Date**: 2026-08-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/012-isolated-analysis-workspaces/spec.md`

## Summary

Route CLI analysis through the existing workspace worker, reuse the detached-worktree history walker, and bind the worker to the existing repository-local DuckDB path. When the requested branch differs from the branch recorded in the store, the worker automatically rebuilds that store instead of failing with `Branch changed ...; rerun with --rebuild`. The user's active checkout remains untouched, and existing VS Code/dashboard clients keep discovering the same file.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Existing Click CLI, Git CLI, DuckDB, msgspec worker runtime, FastAPI server

**Storage**: Existing `<repo>/.ppi/history.duckdb`, holding the most recently analyzed branch

**Testing**: Focused pytest CLI integration and worker IPC regressions plus existing related branch/worktree tests

**Target Platform**: Local macOS and Linux development environments with Git

**Project Type**: Existing Python CLI with local worker and optional dashboard

**Performance Goals**: N/A; this feature changes orchestration only and adds no analysis-performance requirement

**Constraints**: Active checkout is read-only; committed history only; one branch report at a time; no new dependency, store, or service

**Scale/Scope**: Sequential analysis of any local branch into the repository's existing report store

## Constitution Check

*GATE: Passed before and after design.*

| Principle | Minimal design | Status |
|---|---|---|
| Functional Core, OO Shell | Branch/path derivation is pure; existing Git/worktree and worker shells perform effects. | PASS |
| Layered Core Independence | CLI delegates analysis to the worker; the analysis core remains delivery-neutral. | PASS |
| Plugin Extensibility | Profile remains an input; analyzer/plugin behavior is unchanged. | PASS |
| CLI-First | CLI remains the user interface but sends analysis commands through the shared worker boundary. | PASS |
| Single Writer | The worker is the only writer and uses the existing repository writer lock and store. | PASS |
| Typed Contracts | Existing context already carries the requested branch; no new domain abstraction is added. | PASS |

No exception or new architectural layer is required.

## Current Cause

- The history walker already creates a detached worktree, so it does not need to switch the user's branch.
- Existing clients discover `<repo>/.ppi/history.duckdb`, so moving the store would require unrelated client changes.
- Direct CLI and worker flows currently disagree on store ownership and location.
- The analyzer rejects a different requested branch unless the user explicitly passes `--rebuild`.
- Therefore analysis stored for `dev` blocks a normal request for `CMRT-361` even though the detached worktree itself is suitable.

## Minimal Implementation

1. Resolve the requested branch before any store write. Default to the active branch when omitted.
2. Make CLI analysis start or attach the workspace worker and include the resolved requested branch in the existing `analysis.start` call; remove direct CLI ownership of writes.
3. Extend the existing worker client payload with `branch`, have `WorkerRuntime` read it, and pass it to `AnalysisService.run()`.
4. Bind `WorkerRuntime` and `AnalysisService` to `<repo>/.ppi/history.duckdb`; keep `--analysis-dir` for worker runtime and detached-worktree artifacts only.
5. Resolve and validate the supplied branch in `AnalysisService` before opening the writer.
6. If the stored branch matches, keep the current incremental path.
7. If the stored branch differs, select the existing destructive rebuild path automatically instead of raising the branch-mismatch error.
8. Keep the existing detached-worktree walker, `--branch` interface, temporary analysis directory, cleanup, store schema, and report path unchanged.
9. After a successful rebuild, the same store identifies the requested branch and contains only its report. A failed rebuild is allowed to leave the previous report unavailable, matching the existing explicit `--rebuild` contract.

## Project Structure

### Documentation

```text
specs/012-isolated-analysis-workspaces/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/cli.md
```

### Expected source changes

```text
src/ppi/
├── cli/main.py
├── worker_ipc/client.py
├── worker_ipc/worker_runtime.py
└── worker_ipc/analysis_service.py

tests/
├── unit/
├── integration/
└── worker_ipc/
```

**Structure Decision**: Reuse the existing gateway, `analysis.start` payload, worker, store-path helper, rebuild path, and worktree lifecycle. Add one `branch` payload field and change only its existing CLI/client/runtime/service call chain. Add no new command, path resolver, domain entity, schema, subsystem, or report-reader change.

## Delivery Sequence

1. Route CLI analysis through the existing worker and carry the requested branch through the existing IPC request.
2. Bind that worker to the repository-local store and use the supplied branch in `AnalysisService`.
3. Change worker branch mismatch from an error into automatic use of the existing rebuild path.
4. Add one regression flow: analyze `dev`, then `CMRT-361` without `--rebuild`, while the active dirty checkout remains unchanged; verify the same store now reports `CMRT-361`.
5. Analyze `CMRT-361` again and verify the existing incremental path is reused.
