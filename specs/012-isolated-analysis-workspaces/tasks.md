# Tasks: Non-Blocking Branch Analysis

**Input**: Design documents from `specs/012-isolated-analysis-workspaces/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/cli.md`, `quickstart.md`

**Tests**: Required by the specification. Write the focused regression tests first and confirm they fail for the branch-mismatch behavior before implementation.

**Organization**: The feature has one P1 user story and one minimal implementation slice.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it changes a different file
- **[US1]**: Analyze any requested branch without switching the user's checkout

## Phase 1: Setup

**Purpose**: Reuse the existing CLI, worker, repository-local store, writer lock, and detached-worktree infrastructure.

No setup changes are required.

---

## Phase 2: Foundational

**Purpose**: Confirm no new schema, dependency, path resolver, store, or worktree lifecycle is needed.

No foundational changes are required.

---

## Phase 3: User Story 1 - Analyze Any Branch Without Switching the User Checkout (Priority: P1) 🎯 MVP

**Goal**: Analyze a requested branch through the existing detached worktree; automatically rebuild the existing `.ppi/history.duckdb` when its recorded branch differs; keep same-branch runs incremental; leave the active checkout unchanged.

**Independent Test**: In a disposable dirty checkout on `feature/test`, analyze `dev`, then `feature/test`, then `feature/test` again without manual `--rebuild`; verify the same store follows the requested branch, the third run is incremental, invalid branch input does not change the store, and all active-checkout state remains unchanged.

### Tests for User Story 1

- [X] T001 [P] [US1] Add a failing CLI integration regression covering worker delegation with the requested branch, dirty-checkout preservation, `dev -> feature/test` automatic rebuild, repository-store attribution, same-branch incremental reuse, and invalid-branch no-write behavior in `tests/integration/test_branch_switch_rebuild.py`
- [X] T002 [P] [US1] Add a failing worker regression proving branch payload propagation without substitution by the worker checkout's active branch, repository-local store binding, automatic destructive rebuild on stored-branch mismatch, and incremental reuse on a matching branch in `tests/worker_ipc/test_analysis_service_branch_switch.py`

### Implementation for User Story 1

- [X] T003 [US1] Resolve `ctx.branch` with the existing `git.resolve_branch(ctx.repo, ctx.branch)` before starting analysis, fail before IPC on resolution error, route CLI `analyze` through the existing worker gateway, and pass the concrete branch name to `_analyze_via_worker()` while preserving progress/error behavior in `src/ppi/cli/main.py`
- [X] T004 [US1] Add the requested branch to `WorkerClientProtocol.analysis_start()` and the existing `analysis.start` payload in `src/ppi/worker_ipc/client.py`
- [X] T005 [US1] Read `branch` from the analysis-start payload, bind the store to `store_path(project_path)`, and pass the branch to `AnalysisService.run()` while retaining `analysis_path` for runtime/worktree artifacts in `src/ppi/worker_ipc/worker_runtime.py`
- [X] T006 [US1] Resolve the supplied branch before opening `StoreWriter`, then replace stored-branch mismatch failure with the existing destructive rebuild path while preserving same-branch skip logic in `src/ppi/worker_ipc/analysis_service.py`

**Checkpoint**: User Story 1 is complete when CLI and worker regressions pass with the repository store, without changes to worktree lifecycle, schema, CLI flags, or report-reader implementations.

---

## Phase 4: Verification

**Purpose**: Prove the minimal change and guard against scope growth.

- [X] T007 Run the focused regressions in `tests/integration/test_branch_switch_rebuild.py` and `tests/worker_ipc/test_analysis_service_branch_switch.py`, then execute the existing related branch/worktree tests in `tests/integration/test_edge_cases.py`, `tests/unit/test_git_branch.py`, and the directly affected worker tests under `tests/worker_ipc/`
- [X] T008 Validate the three-command scenario and checkout invariants from `specs/012-isolated-analysis-workspaces/quickstart.md`, then confirm `git diff --check` and that no production files outside `src/ppi/cli/main.py`, `src/ppi/worker_ipc/client.py`, `src/ppi/worker_ipc/worker_runtime.py`, and `src/ppi/worker_ipc/analysis_service.py` changed without newly discovered evidence

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup and Foundational**: No work required.
- **US1 tests**: T001 and T002 can start immediately and run in parallel.
- **US1 implementation**: T003 depends on T001; T004 depends on T002; T005 depends on T004; T006 depends on T005.
- **Verification**: T007 depends on T003 and T006; T008 depends on T007.

### User Story Dependencies

- **User Story 1 (P1)**: Independent; it is the entire MVP.

### Parallel Opportunities

- T001 and T002 modify different test files and can be written in parallel.
- T001 and T002 are the only parallel implementation opportunity; T003-T006 form one small IPC call chain and run in order.

## Parallel Example: User Story 1

```text
Task T001: Add direct CLI branch-switch regression in tests/integration/test_branch_switch_rebuild.py
Task T002: Add worker branch-switch regression in tests/worker_ipc/test_analysis_service_branch_switch.py
```

## Implementation Strategy

### MVP

1. Write T001 and T002 and prove the current branch-mismatch failures.
2. Apply T003-T006 through the existing IPC, worker, and rebuild paths.
3. Run T007 and T008.

No later user stories or speculative follow-up work are part of this feature.

## Notes

- Do not add a new store, schema, workspace selector, domain model, CLI option, API, or client change.
- Do not change the detached-worktree lifecycle.
- Keep the worker as the only writer to `<repo>/.ppi/history.duckdb`, the single report visible to existing clients.
