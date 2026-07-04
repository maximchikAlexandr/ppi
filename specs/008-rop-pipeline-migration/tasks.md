# Tasks: Railway Oriented Pipeline Migration

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/` for `008-rop-pipeline-migration`  
**Feature**: Full migration of covered Python and TypeScript runtime/read processes to Railway Oriented Programming  
**Generated**: 2026-07-04  
**Hardened**: 2026-07-04 after cross-artifact analysis and implementation-handoff checklist

## Summary

This task list is intentionally ambitious. A task is not complete when it only adds a `pipe(...)` wrapper around an unchanged imperative function. Completion requires named stages, typed success/failure contracts, explicit effect/framework adapters, characterization coverage, and cleanup of temporary compatibility wrappers.

Repository path grounding is mandatory. Current public repository layout uses `src/ppi/core`, `src/ppi/history`, `src/ppi/adapters`, `src/ppi/cli`, `frontend/src/api`, `frontend/src/transforms`, `frontend/src/pages`, and `frontend/src/components`. Do **not** create invented namespaces such as `src/ppi/analysis` or `frontend/src/features` unless T017-T019 inventory first proves the repository has been reorganized and records the new canonical paths.

## Phase 1: Setup

- [X] T001 Confirm existing Python `Expression` dependency and typing support in `pyproject.toml`; do not add `returns`
- [X] T002 Add TypeScript Effect dependency and lockfile updates in `frontend/package.json`
- [X] T003 Add TypeScript Effect dependency and lockfile updates in `vscode-extension/package.json`
- [X] T004 [P] Create Python ROP package skeleton in `src/ppi/rop/__init__.py`
- [X] T005 [P] Create TypeScript shared ROP package skeleton in `frontend/src/rop/index.ts`
- [X] T006 [P] Create VS Code ROP adapter package skeleton in `vscode-extension/src/rop/index.ts`
- [X] T007 Add Python type-check configuration for the selected ROP library in `pyproject.toml`
- [X] T008 Add frontend and extension typecheck scripts for ROP validation in `frontend/package.json` and `vscode-extension/package.json`
- [X] T009 Document the anti-cosmetic migration rule and repository path guardrails in `specs/008-rop-pipeline-migration/quickstart.md`

## Phase 2: Foundational Prerequisites

- [X] T010 Define Python `PipelineStage`, `StageResult`, async-stage result aliases, and stage-name aliases around `Expression` in `src/ppi/rop/types.py`
- [X] T011 Define Python typed error taxonomy in `src/ppi/rop/errors.py`
- [X] T012 Define Python adapter helpers for exception-to-error and effect boundaries in `src/ppi/rop/adapters.py`
- [X] T013 Define Python stage composition conventions and compatibility adapter helpers in `src/ppi/rop/pipeline.py`
- [X] T014 [P] Define TypeScript `PipelineStage`, `PipelineError`, `DecodeMappingFailure`, and view-model error types in `frontend/src/rop/types.ts`
- [X] T015 [P] Define TypeScript Effect adapter helpers for transport/decode/domain mapping in `frontend/src/rop/effect.ts`
- [X] T016 [P] Define VS Code `BridgeFailure`, cancellation, progress-decode, and process adapter error types in `vscode-extension/src/rop/types.ts`
- [X] T017 Create migration inventory from the contract template in `specs/008-rop-pipeline-migration/handoff/implementation-decisions.md`
- [X] T018 Fill initial inventory for all covered Python `src/ppi/core` and `src/ppi/history` pipelines in `specs/008-rop-pipeline-migration/handoff/implementation-decisions.md`
- [X] T019 Fill initial inventory for covered frontend and VS Code paths in `specs/008-rop-pipeline-migration/handoff/implementation-decisions.md`
- [X] T020 Add repository-wide stage contract checklist in `specs/008-rop-pipeline-migration/checklists/implementation-handoff.md`
- [X] T021 Add compatibility-adapter naming convention, removal policy, and path-change policy in `specs/008-rop-pipeline-migration/contracts/pipeline-stage-contract.md`
- [X] T022 Create shared Python characterization fixture for representative analysis output and backend query/RPC contract snapshots in `tests/characterization/test_analysis_output_equivalence.py`
- [X] T023 Create shared frontend fixture for valid and invalid API/RPC responses in `frontend/src/api/__fixtures__/analysisResponses.ts`
- [X] T024 Create VS Code bridge fixture for progress events and bridge failures in `vscode-extension/src/test/fixtures/progressEvents.ts`

## Phase 3: User Story 1 - Backend analysis runs through typed ROP stages (P1)

**Goal**: Convert the central Python Odoo analysis axis into real typed ROP stages while preserving output behavior.

**Independent Test**: Running the normal analysis for a representative repository produces equivalent output; invalid addons path returns typed validation failure; no covered analysis core path remains only a top-level pipe wrapper.

- [X] T025 [US1] Locate current core analysis entrypoints under `src/ppi/core/` and record exact current files/functions in `specs/008-rop-pipeline-migration/handoff/implementation-decisions.md`
- [X] T026 [US1] Add success characterization test for `odoo_project_analysis_pipeline` in `tests/characterization/test_odoo_project_analysis_pipeline.py`
- [X] T027 [US1] Add invalid addons path typed failure test in `tests/core/test_addons_path_validation_pipeline.py`
- [X] T028 [US1] Extract report config stage into `src/ppi/core/pipelines/odoo_project.py`
- [X] T029 [US1] Convert addons path resolution and validation to a `Result`-returning stage in `src/ppi/core/pipelines/addons_paths.py`
- [X] T030 [US1] Wrap filesystem path checks as effect adapters in `src/ppi/adapters/filesystem.py`
- [X] T031 [US1] Convert module discovery entrypoint to `Expression` `Result` stage contracts in `src/ppi/core/pipelines/module_discovery.py`
- [X] T032 [US1] Extract manifest read adapter and manifest parse stage in `src/ppi/core/pipelines/module_discovery.py`
- [X] T033 [US1] Convert duplicate module resolution to a pure stage in `src/ppi/core/pipelines/module_discovery.py`
- [X] T034 [US1] Convert provider map attachment to a typed stage in `src/ppi/core/pipelines/provider_index.py`
- [X] T035 [US1] Convert coupling edge attachment and scoring to typed stages in `src/ppi/core/pipelines/coupling_edges.py`
- [X] T036 [US1] Convert freeze/export to typed final stage in `src/ppi/core/pipelines/export.py`
- [X] T037 [US1] Compose `odoo_project_analysis_pipeline` from named stages in `src/ppi/core/pipelines/odoo_project.py`
- [X] T038 [US1] Keep old analysis entrypoint as compatibility adapter only in `src/ppi/core/compat.py`
- [X] T039 [US1] Add CLI integration adapter for the analysis railway in `src/ppi/cli/rop_integration.py` and update the current CLI command file recorded by T025
- [X] T040 [US1] Update typed error-to-CLI/progress mapping for analysis failures in `src/ppi/cli/rop_integration.py`
- [X] T041 [US1] Mark migrated analysis stages and remaining shells in `specs/008-rop-pipeline-migration/handoff/implementation-decisions.md`

## Phase 4: User Story 2 - Main Python analysis-core subpipelines are explicit and composable (P1)

**Goal**: Turn module enrichment, metrics, complexity, AST facts, and model expression resolution into nested typed subpipelines.

**Independent Test**: Module enrichment succeeds for valid modules; malformed Python/manifest inputs are represented as recoverable domain data where applicable; AST visitor objects do not leak into pipeline state.

- [X] T042 [US2] Add module enrichment success and parse-failure characterization tests in `tests/core/test_module_enrichment_pipeline.py`
- [X] T043 [US2] Add model expression resolution table tests in `tests/core/test_model_expression_resolution_pipeline.py`
- [X] T044 [US2] Convert code metrics stage to typed module update stage in `src/ppi/core/pipelines/module_code_metrics.py`
- [X] T045 [US2] Convert file classification and line counting failures to recoverable typed facts in `src/ppi/core/pipelines/module_code_metrics.py`
- [X] T046 [US2] Convert Python complexity analysis to typed stage contracts in `src/ppi/core/pipelines/python_complexity.py`
- [X] T047 [US2] Convert complexity distribution/stat reducers to pure functions in `src/ppi/core/pipelines/python_complexity.py`
- [X] T048 [US2] Extract AST file read/parse adapter from visitor logic in `src/ppi/core/pipelines/python_ast_facts.py`
- [X] T049 [US2] Keep `ast.NodeVisitor` shell internal and expose function-shaped AST facts stage in `src/ppi/core/pipelines/python_ast_facts.py`
- [X] T050 [US2] Extract alias state construction and update rules to pure functions in `src/ppi/core/pipelines/model_expression_resolution.py`
- [X] T051 [US2] Extract env object detection and env-subscript model extraction to pure functions in `src/ppi/core/pipelines/model_expression_resolution.py`
- [X] T052 [US2] Extract target-name and method-call resolution to typed functions in `src/ppi/core/pipelines/model_expression_resolution.py`
- [X] T053 [US2] Compose `module_enrichment_pipeline` from metrics, complexity, and AST facts stages in `src/ppi/core/pipelines/module_enrichment.py`
- [X] T054 [US2] Map unsupported dynamic model expressions to typed recoverable facts in `src/ppi/core/pipelines/model_expression_resolution.py`
- [X] T055 [US2] Update provider and edge stages to consume prepared facts instead of rescanning module state ad hoc in `src/ppi/core/pipelines/provider_index.py` and `src/ppi/core/pipelines/coupling_edges.py`
- [X] T056 [US2] Remove or demote old enrichment imperative wrapper in `src/ppi/core/compat.py`
- [X] T057 [US2] Update inventory status for enrichment, AST facts, and model expression pipelines in `specs/008-rop-pipeline-migration/handoff/implementation-decisions.md`

## Phase 5: User Story 5 - Migration is incremental and safe / Python history effects (P2)

**Goal**: Migrate history/effect orchestration and persistence/progress boundaries after the core analysis railway exists, without pretending Git/worktree/filesystem/process effects are pure.

**Independent Test**: Invalid repo/branch/worktree failures return typed orchestration errors; per-commit behavior remains equivalent or explicitly documented; progress reporting derives from typed outcomes.

- [X] T058 [US5] Add history walk characterization tests for commit selection and representative progress in `tests/history/test_history_walk_pipeline.py`
- [X] T059 [US5] Add Git/worktree failure tests in `tests/history/test_history_orchestration_failures.py`
- [X] T060 [US5] Extract git history ingestion adapter in `src/ppi/history/pipelines/git_history_ingestion.py`
- [X] T061 [US5] Extract pure history plan stage in `src/ppi/history/pipelines/history_plan.py`
- [X] T062 [US5] Extract worktree prepare and checkout effect adapters in `src/ppi/history/pipelines/worktree_checkout.py`
- [X] T063 [US5] Extract commit iteration railway and per-commit error policy in `src/ppi/history/pipelines/history_walk.py`
- [X] T064 [US5] Wrap per-commit analysis call as adapter to `odoo_project_analysis_pipeline` in `src/ppi/history/pipelines/history_walk.py`
- [X] T065 [US5] Map persistence/export/progress effects to typed adapters in `src/ppi/history/pipelines/history_walk.py`
- [X] T066 [US5] Update existing history walk entrypoint to delegate to the history railway in `src/ppi/history/walker.py`; if the current entrypoint differs, record the exact file in inventory before editing
- [X] T067 [US5] Update Python CLI JSON progress event emission to use typed stage outcomes in `src/ppi/cli/progress.py`
- [X] T068 [US5] Document fail-fast, skip-with-report, and abort-with-context behavior in `specs/008-rop-pipeline-migration/contracts/pipeline-stage-contract.md`
- [X] T069 [US5] Update inventory status for history, git ingestion, plan, and worktree checkout pipelines in `specs/008-rop-pipeline-migration/handoff/implementation-decisions.md`

## Phase 6: User Story 3 - TypeScript frontend read and view-model flows use ROP-style pipelines (P2)

**Goal**: Make API/RPC read, schema decode, DTO mapping, dashboard derivation, and graph derivation typed and composable outside React components.

**Independent Test**: Valid snapshots render the same dashboard/graph data; transport, schema, and domain mapping failures are distinguishable typed errors; components receive ready view models rather than raw DTOs.

- [X] T070 [US3] Add API/RPC read pipeline tests for valid response, transport error, schema error, and mapping error in `frontend/src/api/readPipeline.test.ts`
- [X] T071 [US3] Add dashboard view-model derivation tests for valid, empty, and partial data in `frontend/src/transforms/dashboardViewModel.test.ts`
- [X] T072 [US3] Add graph view-model derivation tests for valid graph, empty graph, and invalid edge data in `frontend/src/transforms/graphViewModel.test.ts`
- [X] T073 [US3] Implement request builder stage in `frontend/src/api/readPipeline.ts`
- [X] T074 [US3] Implement transport Effect adapter in `frontend/src/api/readPipeline.ts`
- [X] T075 [US3] Implement schema decode stage and typed decode errors in `frontend/src/api/readPipeline.ts`
- [X] T076 [US3] Implement DTO-to-domain mapping stage in `frontend/src/api/readPipeline.ts`
- [X] T077 [US3] Implement UI-safe read error mapping stage in `frontend/src/api/readPipeline.ts`
- [X] T078 [US3] Update covered API/RPC clients to call the read railway in `frontend/src/api/client.ts`
- [X] T079 [US3] Extract snapshot/history normalization stage in `frontend/src/transforms/dashboardViewModel.ts`
- [X] T080 [US3] Extract dashboard metrics and aggregate builders in `frontend/src/transforms/dashboardViewModel.ts`
- [X] T081 [US3] Extract dashboard table rows, treemap nodes, timelapse series, and formatting stages in `frontend/src/transforms/dashboardViewModel.ts`
- [X] T082 [US3] Update current dashboard page/component shells recorded in inventory to render supplied view models/errors under `frontend/src/pages/` or `frontend/src/components/`
- [X] T083 [US3] Extract graph normalization, edge labels, visible-edge filtering, detail rows, and viewport stages in `frontend/src/transforms/graphViewModel.ts`
- [X] T084 [US3] Update current graph page/component shells recorded in inventory to render supplied view models/errors under `frontend/src/pages/` or `frontend/src/components/`
- [X] T085 [US3] Remove inline DTO decoding and core aggregation from covered React page/component shells under `frontend/src/pages/` and `frontend/src/components/`
- [X] T086 [US3] Update frontend inventory entries for API read, dashboard view-model, and graph view-model pipelines in `specs/008-rop-pipeline-migration/handoff/implementation-decisions.md`

## Phase 7: User Story 4 - VS Code bridge stays an orchestration boundary (P2)

**Goal**: Keep VS Code/process/webview lifecycle code as a boundary while exposing typed function adapters for settings, command build, spawn, progress decode, RPC startup, cancellation, and webview handoff.

**Independent Test**: CLI spawn failure, malformed progress event, RPC startup failure, and cancellation each produce typed bridge errors while existing commands remain green.

- [X] T087 [US4] Add bridge adapter tests for settings resolution, command build, spawn failure, malformed progress, RPC failure, and cancellation in `vscode-extension/src/bridge/analysisBridge.test.ts`
- [X] T088 [US4] Extract workspace/settings resolution stage in `vscode-extension/src/bridge/analysisBridgePipeline.ts`
- [X] T089 [US4] Extract CLI command build stage in `vscode-extension/src/bridge/analysisBridgePipeline.ts`
- [X] T090 [US4] Wrap process spawn as typed Effect adapter in `vscode-extension/src/bridge/analysisBridgePipeline.ts`
- [X] T091 [US4] Implement progress event stream decoder with typed malformed-event errors in `vscode-extension/src/bridge/progressDecode.ts`
- [X] T092 [US4] Wrap RPC datasource startup as typed bridge adapter in `vscode-extension/src/bridge/analysisBridgePipeline.ts`
- [X] T093 [US4] Model cancellation as typed bridge/orchestration outcome in `vscode-extension/src/bridge/analysisBridgePipeline.ts`
- [X] T094 [US4] Extract webview state handoff adapter in `vscode-extension/src/bridge/webviewHandoff.ts`
- [X] T095 [US4] Update existing extension command handlers to call `vscode_analysis_bridge_pipeline` in `vscode-extension/src/extension.ts`
- [X] T096 [US4] Preserve VS Code lifecycle shells and document them in `specs/008-rop-pipeline-migration/handoff/implementation-decisions.md`

## Phase 8: Polish and Cross-Cutting Concerns

- [X] T097 Remove or isolate deprecated custom pipe helpers and conflicting `toolz.pipe` usage in `src/ppi/core` and `src/ppi/history`
- [X] T098 Remove temporary Python compatibility adapters that are no longer justified in `src/ppi/core/compat.py`
- [X] T099 Remove temporary frontend and VS Code compatibility wrappers in `frontend/src/api/client.ts` and `vscode-extension/src/bridge/analysisBridgePipeline.ts`
- [X] T100 Add anti-cosmetic architecture tests or static checks for large unchanged imperative wrappers in `tests/architecture/test_rop_migration_bar.py`
- [X] T101 Add documentation for writing Python ROP stages in `specs/008-rop-pipeline-migration/contracts/pipeline-stage-contract.md`
- [X] T102 Add documentation for writing TypeScript Effect/Either stages in `specs/008-rop-pipeline-migration/contracts/pipeline-stage-contract.md`
- [X] T103 Add documentation for wrapping React, VS Code, AST, filesystem, Git, RPC, and storage shells in `specs/008-rop-pipeline-migration/contracts/pipeline-stage-contract.md`
- [X] T104 Update project developer guide with migration commands and validation workflow in `docs/development.md`
- [X] T105 Run and fix Python tests/type checks for the migrated ROP code in `pyproject.toml`
- [X] T106 Run and fix frontend tests/type checks/build for the migrated ROP code in `frontend/package.json`
- [X] T107 Run and fix VS Code extension tests/type checks/build for the migrated ROP code in `vscode-extension/package.json`
- [X] T108 Complete final inventory review and mark remaining shells as intentional in `specs/008-rop-pipeline-migration/handoff/implementation-decisions.md`
- [X] T109 Verify the anti-cosmetic completion contract against all covered pipelines in `specs/008-rop-pipeline-migration/checklists/implementation-handoff.md`
- [X] T110 Update release notes or migration notes for maintainers in `specs/008-rop-pipeline-migration/handoff/implementation-decisions.md`

## Dependencies

### Phase Dependencies

- Phase 1 must complete before Phase 2.
- Phase 2 blocks every user-story phase because it defines common vocabulary, error types, adapters, inventory, fixtures, and path grounding.
- Phase 3 and Phase 4 are both P1 backend work; Phase 4 depends on the core stage/error vocabulary from Phase 2 and benefits from Phase 3, but metrics/AST extraction tasks can start once shared types exist.
- Phase 5 starts after Phase 3 exposes `odoo_project_analysis_pipeline` as a stable adapter target.
- Phase 6 can start after TypeScript foundation tasks T014-T015 and fixture T023 are done.
- Phase 7 can start after VS Code foundation task T016 and fixture T024 are done; it also depends on the Python JSON progress semantics from Phase 5.
- Phase 8 starts after all story phases have completed their cleanup handoff.

### Story Dependencies

- **US1** is the MVP foundation: central Python analysis core.
- **US2** deepens US1 and should follow or overlap only after US1 has established the new core pipeline package boundaries.
- **US5** depends on US1 because history walk calls analysis per commit.
- **US3** depends on stable API/domain outputs but can proceed using existing fixtures if backend work is still in progress.
- **US4** depends on Python CLI/progress outcome shapes and VS Code ROP error types.

### Blocking Tasks

- T010-T013 block Python ROP migration tasks.
- T014-T015 block frontend ROP migration tasks.
- T016 blocks VS Code bridge migration tasks.
- T017-T019 block any task that changes target paths or creates compatibility adapters.
- T022 blocks safe backend behavior-preserving refactors.
- T023 blocks frontend read/view-model migration.
- T024 blocks VS Code progress/bridge migration.

## Parallel Execution Examples

```text
# After Phase 2 foundations are complete:
T026 and T027 can be implemented in parallel with T028-T033 by separate engineers.
T044-T047 can proceed in parallel with T048-T052 after T042-T043 are defined.
T070-T072 can proceed in parallel because they touch independent frontend test files.
T088-T091 can proceed in parallel with T092-T094 after T087 defines expected bridge behavior.
```

```text
# Documentation and inventory can run alongside code slices:
T041, T057, T069, T086, and T096 can be updated by the owner of each slice.
T101-T103 can start once at least one Python, one TS, and one boundary adapter example exists.
```

## MVP Scope

The MVP is **Phase 1 + Phase 2 + Phase 3**:

1. Shared ROP vocabulary and anti-cosmetic rules exist.
2. `odoo_project_analysis_pipeline` is a true composition of typed stages.
3. Valid analysis output remains equivalent.
4. Invalid addons path and at least one core validation failure return typed failures.
5. Remaining shells and compatibility adapters are inventoried rather than hidden.
6. Target paths are grounded in the current repository layout before code movement starts.

This MVP is enough to prove the migration is real before expanding into enrichment, history, frontend, and VS Code.

## Independent Test Criteria by Story

- **US1**: Representative backend analysis output equivalence; invalid addons path typed failure; no top-level-only ROP wrapper around old analysis core.
- **US2**: Enrichment succeeds for valid modules; file/module-level parse failure is recoverable; AST visitor remains shell-only; model expression resolution is tested as pure typed functions.
- **US5**: History walk preserves commit selection/progress behavior; Git/worktree failures are typed orchestration failures; per-commit analysis delegates to the new analysis railway.
- **US3**: Valid API/RPC data maps to the same dashboard/graph view models; transport/schema/mapping failures are distinguishable; components render prepared view models/errors.
- **US4**: VS Code command flow handles settings, spawn, malformed progress, RPC startup, cancellation as typed bridge outcomes while preserving current command behavior.

## Format Validation

All task items use the required checklist format with task IDs. Story-phase tasks include `[US#]`. Parallelizable tasks use `[P]` only when they touch independent files and do not depend on incomplete tasks in the same phase. Every implementation task names a concrete file or repository directory path, and every directory-scoped task must record the exact current file paths in the migration inventory before editing code.
