# Feature Specification: Railway Oriented Pipeline Migration

**Feature Branch / Spec ID**: `008-rop-pipeline-migration`  
**Created**: 2026-07-04  
**Status**: Implementation-ready after analysis/checklist hardening  
**Input**: Request to plan a full migration of the main Python and TypeScript processes in `maximchikAlexandr/ppi` to Railway Oriented Programming (ROP), using established FP libraries instead of custom handwritten pipe primitives where practical.

## Overview

Migrate the core runtime and read-model processes of Python Project Inspector to a Railway Oriented Programming style so that major analysis, history, export, API-read, view-model, and bridge flows are expressed as typed, composable pipelines with explicit success/failure channels.

The migration must cover the main business/runtime processes end-to-end where they are already pipeline-shaped, while keeping framework-bound object primitives at the boundary. Framework-specific objects, visitors, CLI/webview/RPC adapters, process spawning, filesystem, Git, HTTP/RPC, and React rendering primitives may remain object-oriented or imperative internally, but they must expose function-shaped adapters where the main flow needs to call them from a pipeline.

## Goals

- Make primary Python and TypeScript processes readable as explicit pipelines of named stages.
- Replace scattered exception/null/imperative branching in core flows with typed Result/Either-style error propagation.
- Use existing or selected mature FP/ROP libraries for pipe, flow, Result/Either, async/effect composition, and error mapping instead of creating a project-specific pipe abstraction first.
- Preserve current behavior and public contracts during migration.
- Keep framework-specific or object-native integration code at the edge unless wrapping it is required to join a pipeline.


## Full Migration Bar

This feature is a full ROP migration for the covered core flows, not a cosmetic wrapper around the current imperative implementation. A process is **not** considered migrated when a top-level `pipe(...)` or `flow(...)` only calls one large imperative function whose internal success path, failure path, mutation, exception handling, and framework leakage remain unchanged.

Completion requires that each covered primary process exposes its main happy path and failure path as an explicit railway composition of named stages. The old imperative call stack may survive only as a temporary compatibility adapter or as an intentional effect/framework shell.

### Mandatory Refactoring Depth

- The main Python analysis flow MUST NOT remain a single imperative orchestration function with a pipeline-shaped wrapper around it.
- The main TypeScript read/view-model flow MUST NOT remain hidden inside React lifecycle, component state handlers, or ad hoc Promise chains with a pipeline-shaped wrapper around it.
- Each major backend and frontend stage MUST expose a typed stage contract: input state, success output, typed failure output, and adapter boundary when effects are involved.
- Existing imperative/object code MAY remain only when it is a framework, lifecycle, visitor, process, transport, storage, or UI shell; the shell MUST be callable through a small function adapter from the railway.
- Ad hoc exception handling inside covered core flows MUST be replaced by typed failure mapping unless the exception is intentionally contained inside an adapter.
- Recoverable per-file/per-module analysis failures MUST flow as domain data; unrecoverable orchestration failures MUST short-circuit the railway.
- Existing custom or handwritten pipe helpers MUST be removed, deprecated, or isolated where the selected FP library provides equivalent pipe/flow/result/effect primitives.
- The migration MUST produce visible architectural simplification: named stages, explicit typed errors, reduced hidden mutation, and no framework-object leakage across core pipeline boundaries.

### Anti-Cosmetic Acceptance Rule

No covered primary process is considered migrated while its main flow is merely wrapped by a top-level pipe but still relies internally on untyped exceptions, nullable sentinels, hidden mutation, implicit global dependencies, or framework objects leaking across core pipeline boundaries.

## Non-Goals

- Rewriting all framework, UI, CLI, AST visitor, or transport internals into pure FP code.
- Replacing React, VS Code extension APIs, CLI framework objects, AST visitors, subprocess objects, or storage drivers.
- Introducing a new custom FP framework for the project.
- Changing output schemas, JSON-RPC contracts, persisted history format, or dashboard behavior as part of this feature.

## Repository Path Guardrails

Implementation tasks MUST be grounded in the repository layout before code movement starts. The current target path families are:

- Python core analysis pipeline code: `src/ppi/core/pipelines/`.
- Python shared ROP vocabulary: `src/ppi/rop/`.
- Python effect/adapters shared across core/history: `src/ppi/adapters/`.
- Python history orchestration pipelines: `src/ppi/history/pipelines/`.
- Python CLI integration/progress mapping: current modules under `src/ppi/cli/`; do not assume a single `src/ppi/cli.py` file.
- TypeScript shared ROP vocabulary: `frontend/src/rop/`.
- TypeScript API/RPC read stages: `frontend/src/api/`.
- TypeScript dashboard/graph derived view-model stages: `frontend/src/transforms/`.
- React rendering/lifecycle shells: current files under `frontend/src/pages/` and `frontend/src/components/`.
- VS Code bridge stages and shell adapters: current files under `vscode-extension/src/`.

The implementer MUST NOT create new namespaces such as `src/ppi/analysis` or `frontend/src/features` merely because a planned pipeline name suggests them. If the repository is reorganized before implementation, the migration inventory MUST first record the new canonical paths and update affected tasks before code is changed.

## Primary Scenarios and Acceptance Tests

### Scenario 1: Backend analysis runs through typed ROP stages

A developer runs the normal analysis flow for an Odoo/Python project. The history walk, worktree checkout boundary, Odoo analysis, module discovery, enrichment, provider indexing, coupling edge detection, and export stages run in the same logical order as before, but each major stage returns a typed success or failure value that can be composed in a pipeline.

**Acceptance checks**:
1. Given a valid repository, the analysis output remains equivalent to the pre-migration output for the same input commit set.
2. Given an invalid addons path, the pipeline stops at the validation stage and returns a typed validation failure instead of throwing an unstructured exception.
3. Given a recoverable module parse or file-level analysis failure, the failure is represented in the existing report/failure model where applicable and does not abort unrelated modules.
4. Given an unrecoverable Git/worktree failure, the history pipeline returns a typed failure with enough context for CLI/VS Code progress reporting.

### Scenario 2: Main Python analysis-core pipelines are explicit and composable

A maintainer opens the Python analysis code and can identify the main stages as reusable functions, not as one large imperative call stack.

**Acceptance checks**:
1. `odoo_project_analysis_pipeline` is represented as a composition of validation, discovery, enrichment, provider index, edge detection, freeze/export stages.
2. `module_enrichment_pipeline` composes code metrics, Python complexity, and AST facts stages.
3. `python_ast_facts_pipeline` keeps AST visitor shells where needed but delegates model expression resolution and facts extraction rules to function-shaped stages.
4. Provider index and coupling edge detection do not rescan global module state ad hoc when a prepared provider index can be passed through the pipeline state.

### Scenario 3: TypeScript frontend read and view-model flows use ROP-style pipelines

A developer modifies frontend data loading or dashboard derivation logic. API/RPC reads, schema decoding, DTO-to-domain mapping, domain normalization, dashboard aggregates, graph view data, table rows, treemap nodes, and timelapse series are represented as composable stages with explicit error channels.

**Acceptance checks**:
1. API/RPC transport errors, schema decode errors, and domain mapping errors are distinguishable.
2. Dashboard and graph view-model stages accept typed domain inputs and return typed derived outputs.
3. UI components receive ready-to-render view models or typed errors, not partially decoded transport DTOs.
4. Existing dashboard tabs continue to render the same data for valid snapshots.

### Scenario 4: VS Code bridge stays an orchestration boundary

A user runs analysis from VS Code. The extension may still use VS Code APIs, process spawning, JSON progress events, RPC, and webview state imperatively, but the bridge has clear functional wrappers for the parts that feed pipeline-style logic.

**Acceptance checks**:
1. Workspace/settings resolution, CLI spawn, progress event decoding, RPC datasource startup, and webview data handoff are each isolated as named stages or adapters.
2. Process-bound and webview-bound code is not forced into pure FP if doing so obscures lifecycle handling.
3. Errors crossing the VS Code boundary are mapped into typed bridge errors before reaching UI status handling.

### Scenario 5: Migration is incremental and safe

A maintainer can migrate one pipeline subtree at a time without a big-bang rewrite.

**Acceptance checks**:
1. Each migrated pipeline subtree has characterization tests before or together with refactoring.
2. Existing CLI, RPC, frontend build, and VS Code build workflows remain green after each migration slice.
3. Adapters allow old imperative functions and new ROP stages to coexist during migration.
4. A temporary compatibility layer is documented and removed or minimized before completion.

## Functional Requirements

- **FR-001**: The system MUST define a canonical ROP migration boundary between core pipeline logic and effect/framework shells.
- **FR-002**: The system MUST represent major pipeline outcomes with typed success/failure containers rather than unstructured exceptions or nullable sentinel values.
- **FR-003**: The system MUST use the existing Python `Expression` dependency for `Result`, `Option`, and typed `pipe` semantics; TypeScript MUST use `Effect` for async/effect/read/bridge flows and plain typed functions or Effect `Either`/`Option` primitives for pure derivation stages. Custom pipe/result/effect helpers are allowed only as thin aliases around those selected libraries.
- **FR-004**: Python pipeline stages MUST be expressible as functions that compose through `Expression` `Result`/`Option` values and typed adapter functions where effects or failures are involved.
- **FR-005**: TypeScript pipeline stages MUST be expressible as functions that compose through a common Result/Either/Effect-style vocabulary where sync, async, or effectful failures are involved.
- **FR-006**: Framework-bound object primitives MAY remain object-oriented internally, but any object-bound operation used by a core pipeline MUST have a small function-shaped adapter.
- **FR-007**: Existing public outputs, persisted data contracts, progress event shapes, JSON-RPC query results, and dashboard-visible semantics MUST remain backward compatible unless explicitly versioned outside this feature.
- **FR-008**: The migration MUST cover the main Python backend analysis axis: history walk, Odoo project analysis, module discovery, module enrichment, provider indexing, coupling edge detection, and export.
- **FR-009**: The migration MUST cover the main TypeScript read/UI axis: API/RPC read, schema decode, DTO/domain mapping, dashboard view-model derivation, graph view derivation, and bridge-facing error mapping.
- **FR-010**: The AST visitor and other naturally object-oriented framework shells MUST be treated as effect/object shells and not rewritten purely for style unless required for testability or composition.
- **FR-011**: Error types MUST preserve actionable context, including stage name, input identity where safe, underlying cause, and recovery/reporting intent.
- **FR-012**: Recoverable domain failures MUST remain data in the analysis result when the current product expects partial results, while unrecoverable orchestration failures MUST short-circuit the relevant railway.
- **FR-013**: Pipeline stage names MUST align with the existing domain vocabulary so logs, tests, docs, and developer discussion can use the same terms.
- **FR-014**: Each migrated pipeline MUST have tests that verify success path, typed failure path, and adapter behavior at framework/effect boundaries.
- **FR-015**: The migration MUST include documentation explaining how to write a new stage, how to adapt an imperative function, and how to map errors.
- **FR-016**: The migration MUST avoid hidden global state in core stages; required dependencies MUST be passed explicitly through context/config/state objects or library-supported dependency mechanisms.
- **FR-017**: The migration MUST keep stage inputs and outputs immutable or replacement-based at core pipeline boundaries.
- **FR-018**: The migration MUST include a deprecation/removal path for old handwritten pipe helpers if any overlap with selected library primitives.

- **FR-019**: The migration MUST reject cosmetic ROP wrappers; each covered major process MUST be decomposed into independently testable named stages with typed success/failure contracts.
- **FR-020**: The migration MUST classify every remaining imperative/object-oriented block in a covered flow as either a temporary compatibility adapter or an intentional effect/framework shell.
- **FR-021**: The migration MUST include a removal plan for compatibility adapters that only exist to bridge old imperative internals during the refactor.
- **FR-022**: The migration MUST move TypeScript decoding, normalization, and view-model derivation out of UI components into pipeline stages before marking frontend migration complete.
- **FR-023**: The migration MUST make typed error propagation observable in tests: at least one short-circuit failure and one recoverable-domain-failure case per major pipeline family.
- **FR-024**: Every implementation target path MUST either use an existing repository parent directory or be introduced by an explicit setup task; invented namespaces MUST be rejected until the migration inventory is updated.

## Pipeline Coverage Requirements

### Python backend pipelines

- `history_walk_analysis_pipeline`
- `git_history_ingestion_pipeline`
- `history_plan_pipeline`
- `worktree_checkout_pipeline`
- `odoo_project_analysis_pipeline`
- `addons_path_validation_pipeline`
- `odoo_module_discovery_pipeline`
- `module_enrichment_pipeline`
- `module_code_metrics_pipeline`
- `python_complexity_analysis_pipeline`
- `python_ast_facts_pipeline`
- `model_expression_resolution_pipeline`
- `provider_index_pipeline`
- `coupling_edge_detection_pipeline`
- `analysis_freeze_export_pipeline`

### TypeScript frontend and bridge pipelines

- `frontend_app_read_pipeline`
- `frontend_api_read_pipeline`
- `frontend_dashboard_viewmodel_pipeline`
- `frontend_graph_view_pipeline`
- `vscode_analysis_bridge_pipeline`

## Error Model Requirements

- Validation errors stop the current pipeline before later stages consume invalid state.
- Domain parse/facts extraction errors that are already modeled as report data remain report data.
- IO/process/transport errors are represented as typed effect failures at the boundary.
- Error mapping is explicit when crossing Python CLI, JSON progress, RPC, TypeScript bridge, and React UI boundaries.
- Logs/progress messages derive from typed stage outcomes instead of duplicating ad hoc exception formatting.

## Edge Cases

- A repository has no commits matching the selected history plan.
- Worktree checkout fails after some commits have already been analyzed.
- Addons paths include missing, duplicate, symlinked, or invalid directories.
- Module discovery sees duplicate module names or malformed manifests.
- Python parsing succeeds for some files and fails for others.
- AST expression resolution sees unsupported dynamic model expressions.
- Provider index is incomplete because providers are declared dynamically.
- Coupling edge detection receives empty modules or zero-score edges.
- RPC returns a valid transport response with invalid or outdated schema.
- Frontend receives partial history/snapshot data while analysis is still running.
- VS Code analysis is cancelled mid-pipeline.

## Success Criteria

- **SC-001**: At least the core Python analysis axis and the frontend read/view-model axis are expressed as documented named pipelines with typed success/failure composition.
- **SC-002**: Existing test suites and build workflows for Python, frontend, and VS Code remain green after migration.
- **SC-003**: For a representative fixture repository, pre- and post-migration analysis outputs are semantically equivalent except for intentionally improved typed error metadata.
- **SC-004**: A new failure-path test exists for each migrated major pipeline.
- **SC-005**: New code avoids project-specific pipe helpers where selected library primitives provide equivalent behavior.
- **SC-006**: Developer documentation includes a stage template and at least one Python and one TypeScript adapter example.

- **SC-007**: No covered primary process is considered migrated while its main flow is merely wrapped by a top-level pipe but still relies internally on untyped exceptions, nullable sentinels, hidden mutation, or framework objects leaking across core pipeline boundaries.
- **SC-008**: At least 80% of covered major pipeline stages have direct tests at the stage-contract level, excluding deliberate effect/framework shells.
- **SC-009**: Every remaining object/imperative shell in the covered flows is listed in the migration inventory with its adapter name and reason for remaining outside the pure/ROP core.
- **SC-010**: Every task-level file or directory target is path-grounded in the current repository layout or explicitly recorded as a newly created path before implementation starts.

## Assumptions

- Python uses the already-present `Expression` dependency for `Result`, `Option`, and typed `pipe`; do not add `returns` or a second Python ROP vocabulary for this feature.
- TypeScript uses `Effect` as the single new primary library for async/resource/error/read/bridge flows; pure derivation stages may stay plain typed functions when they cannot fail.
- Existing `toolz.pipe` usage in Python may be replaced or wrapped if it conflicts with the selected ROP vocabulary.
- Object-oriented framework integration remains acceptable at edges, especially AST visitors, React components, VS Code APIs, subprocess/process management, storage drivers, and CLI framework objects.
- The migration should be delivered in slices, beginning with Python `odoo_project_analysis_pipeline`, then Python history/effects, then TypeScript read/view-model flows, then VS Code bridge polish.

## Key Entities

- **Pipeline Stage**: A named function transforming a typed input to a typed success/failure output.
- **Pipeline State**: Immutable or replacement-based value passed between stages.
- **Typed Error**: Structured failure value with stage context and recovery/reporting intent.
- **Effect Shell**: Boundary code that performs IO, process control, framework API calls, storage access, transport, or UI lifecycle work.
- **Adapter Function**: Small wrapper that exposes object/framework behavior as a function suitable for pipeline composition.
- **Analysis Artifacts**: Intermediate analysis state including modules, metrics, AST facts, providers, edges, scores, and failures.
- **Analysis Batch**: Frozen/export-ready output consumed by storage/query/UI surfaces.
- **Frontend View Model**: Ready-to-render typed data derived from backend snapshots/history.

## Open Clarifications

None. Library choices are fixed for implementation handoff: Python uses existing `Expression`; TypeScript uses `Effect` where a library is needed.
