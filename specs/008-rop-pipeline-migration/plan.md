# Implementation Plan: Railway Oriented Pipeline Migration

**Spec ID**: `008-rop-pipeline-migration`  
**Feature**: Railway Oriented Pipeline Migration  
**Phase**: Plan  
**Date**: 2026-07-04  
**Input Spec**: `specs/008-rop-pipeline-migration/spec.md`

## Executive Summary

This plan treats the ROP migration as a deep architecture refactor of the main Python and TypeScript processes, not as a superficial pipe wrapper. The target state is that the core analysis, read, view-model, and bridge-facing flows are represented as typed railway compositions with explicit success, recoverable-domain-failure, and unrecoverable-failure semantics.

The migration will preserve public behavior and external contracts while replacing implicit imperative control flow with named stages, typed errors, library-provided composition primitives, and function-shaped adapters around framework/object/effect shells.

## Technical Context

### Repository Shape

The project is a mixed Python/TypeScript application with:

- Python package under `src/ppi`.
- React/Mantine dashboard frontend under `frontend`.
- VS Code bridge extension under `vscode-extension`.
- Existing `specs` directory and CLI/build workflows.
- DuckDB-backed history storage under the analyzed repository `.ppi` directory and runtime metadata/worktree/locks under user analysis directories.

### Repository Path Map

Implementation must target the current repository structure rather than inferred feature-style namespaces:

| Concern | Canonical target path family | Notes |
|---|---|---|
| Python core analysis stages | `src/ppi/core/pipelines/` | New pipeline modules for Odoo project analysis, discovery, enrichment, provider index, coupling edges, export. |
| Python shared ROP vocabulary | `src/ppi/rop/` | New cross-cutting types, errors, adapters, composition helpers. |
| Python shared effect adapters | `src/ppi/adapters/` | Use for filesystem/process/Git-style adapters that are shared across core/history. |
| Python history orchestration | `src/ppi/history/pipelines/` | New history railway modules. |
| Python CLI/progress integration | Existing modules under `src/ppi/cli/` | Do not assume `src/ppi/cli.py`; inventory must record exact current CLI file(s). |
| Frontend API/RPC read pipeline | `frontend/src/api/` | Existing API client/schema/data-source area. |
| Frontend derived view models | `frontend/src/transforms/` | New dashboard/graph derivation stages should live with transforms, not in invented `features` folders. |
| Frontend render shells | `frontend/src/pages/`, `frontend/src/components/` | React code remains shell/lifecycle/render boundary. |
| Frontend shared ROP vocabulary | `frontend/src/rop/` | New shared Effect/Either types/helpers. |
| VS Code bridge | Existing modules under `vscode-extension/src/` | Inventory must record exact current command/bridge file(s) before edits. |

Any implementation that wants to create `src/ppi/analysis`, `frontend/src/lib`, or `frontend/src/features` must first update the migration inventory with a deliberate repository reorganization decision.

### Runtime Boundaries

- **Python CLI/runtime**: owns history walk, Git/worktree orchestration, Odoo analysis, module discovery, code metrics, Python complexity, AST facts, provider index, edge detection, export, persistence/query surfaces.
- **TypeScript frontend runtime**: owns API/RPC reads, schema decoding, DTO/domain mapping, dashboard view-models, graph view-models, table/treemap/timelapse derivations, UI error presentation.
- **VS Code extension runtime**: owns workspace/settings resolution, CLI process spawning, progress event reading, RPC datasource startup, webview lifecycle, cancellation, and UI handoff.

### Library Direction

- **Python default**: use the existing `Expression` dependency as the only Python ROP vocabulary for `Result`, `Option`, and typed `pipe`. Do not add `returns` or a second Result/Option representation.
- **TypeScript default**: use `Effect` for bridge/API/read flows where async, resource management, cancellation, typed errors, and service context matter; use plain typed functions or Effect-provided `Either`/`Option` primitives for sync decode/derive stages. Do not add `fp-ts` or `neverthrow` unless a later approved spec changes this feature's library decision.
- **Pipe helpers**: do not create a project-specific pipe abstraction before exhausting selected library primitives. Existing `toolz.pipe` and handwritten helpers are allowed only as compatibility shims during migration.

### Constraints

- No public schema, JSON-RPC, progress event, persisted history, CLI, dashboard, or VS Code command behavior changes unless separately versioned.
- Framework/object shells may remain imperative internally but must not leak across core pipeline boundaries.
- Core stage inputs/outputs should be immutable or replacement-based.
- Error context must be typed and actionable, not just stringified exceptions.
- Incremental slices must keep Python tests, frontend build, VS Code build, and representative analysis output checks green.
- Target paths must be validated against the current repository layout before code is created or moved.

## Constitution Check

Project constitution exists at `.specify/memory/constitution.md` and is applicable. Spec 008 aligns with the functional-core/object-shell rule, layered core independence, single-writer ownership, and typed contracts with explicit `Result`/`Option` error handling. Result: **PASS**. No constitution violations are blocking this plan.

## Architecture Target

### Core Pattern

Each covered pipeline stage follows the same conceptual contract:

```text
StageInput -> Result[StageOutput, TypedStageError]
StageInput -> Result[StageOutput, TypedStageError]          # boundary adapter converts known effect failures
async StageInput -> Result[StageOutput, TypedStageError]    # async boundary adapter returns typed result
```

For TypeScript, the analogous contract is:

```text
StageInput -> Either<TypedStageError, StageOutput>          # pure sync
StageInput -> Effect<StageOutput, TypedStageError, Context> # async/effect/context/resource boundary
```

### Error Categories

- **ValidationFailure**: bad input/config/path/schema; short-circuits before downstream stages.
- **RecoverableDomainFailure**: parse/facts/module-level issue that belongs in analysis output and should not abort unrelated work.
- **OrchestrationFailure**: Git/worktree/process/RPC/cancellation/resource failure; short-circuits the current railway.
- **DecodeMappingFailure**: TypeScript transport/schema/domain conversion failure; reaches UI as typed displayable error.
- **BridgeFailure**: VS Code workspace/settings/process/RPC/webview failure mapped before UI status handling.

### Effect/Object Shell Rule

A remaining object/imperative block is allowed only when it is listed as one of:

1. **Framework shell**: React component, VS Code API object, CLI framework object, AST visitor object.
2. **Effect shell**: filesystem, Git, subprocess, RPC, storage, transport, cancellation, progress stream.
3. **Temporary compatibility adapter**: old imperative function temporarily wrapped while the slice migrates inward.

Everything else must move into named stage functions.

## Migration Slices

### Slice 0: ROP vocabulary and migration inventory

**Goal**: establish shared types, adapters, and anti-cosmetic rules before touching core behavior.

Deliverables:

- Python `pipeline` or `rop` package/module with `Expression` aliases, project error taxonomy, stage aliases, adapter helpers, and docs.
- TypeScript `frontend/src/rop` module with selected library exports, error constructors, stage typing conventions, and docs.
- Inventory of all covered flows, current imperative functions, remaining shells, and target stage names.
- Deprecation plan for old pipe helpers and existing `toolz.pipe` usages that conflict with the new vocabulary.

Exit gates:

- No new custom pipe framework introduced.
- Stage contract template documented.
- Compatibility adapter naming convention documented.

### Slice 1: Python `odoo_project_analysis_pipeline` core

**Goal**: migrate the main analysis-core axis first because it is already pipeline-shaped and central to the project.

Target composition:

```text
build_report_config
-> resolve_and_validate_addons_paths
-> discover_analysis_artifacts
-> enrich_modules_with_code_analysis
-> attach_provider_maps
-> attach_edges_and_scores
-> freeze_and_export_analysis_batch
```

Refactoring depth:

- Split any large orchestration function into stage functions.
- Convert validation, discovery, enrichment, provider, edge, and export outcomes to typed `Expression` `Result` values as appropriate.
- Keep filesystem scanning/reading as effect adapters; keep pure candidate selection, duplicate resolution, parsing, indexing, edge reduction, and scoring as pure stages.
- Preserve current output shape for valid inputs.

Exit gates:

- Stage-contract tests for success and validation failure.
- Characterization fixture comparing pre/post output for a representative repository.
- No top-level-only ROP wrapper around unchanged internals.

### Slice 2: Python module enrichment subtree

**Goal**: make metrics, complexity, AST facts, and model expression resolution a real nested railway.

Target composition:

```text
module_enrichment_pipeline
-> module_code_metrics_pipeline
-> python_complexity_analysis_pipeline
-> python_ast_facts_pipeline
   -> model_expression_resolution_pipeline
```

Refactoring depth:

- Keep `ast.NodeVisitor` shells where they are the natural framework/object primitive.
- Extract env/model expression resolution, alias-state updates, target-name extraction, and provider/fact construction into pure functions returning typed results or recoverable facts.
- Recoverable parse/fact failures remain domain data attached to module/artifact results.

Exit gates:

- File-level parse failure does not abort unrelated modules.
- Unsupported dynamic model expression is represented as typed unsupported/resolution failure or domain warning.
- AST visitor object does not leak as a core pipeline state value.

### Slice 3: Python history/effect orchestration

**Goal**: migrate the outer history walk without pretending Git/worktree/process effects are pure.

Target composition:

```text
git_history_ingestion_pipeline
-> history_plan_pipeline
-> worktree_prepare_pipeline
-> commit_iteration_pipeline
   -> commit_metadata_read_adapter
   -> checkout_commit_adapter
   -> analyze_worktree_adapter / odoo_project_analysis_pipeline
   -> persist/export/progress adapter
```

Refactoring depth:

- Git commands, worktree checkout, filesystem cleanup, progress, and persistence are effect adapters returning typed orchestration failures.
- Plan building and commit selection are pure stages.
- Per-commit failure behavior is explicit: either fail-fast, skip-with-report, or abort-with-context depending on existing semantics.

Exit gates:

- Invalid branch/repo/worktree failure returns typed orchestration failure.
- Partial history behavior is unchanged or explicitly documented.
- VS Code/CLI progress can derive stage/status from typed outcomes.

### Slice 4: TypeScript API/RPC read pipeline

**Goal**: make transport, schema decode, DTO mapping, and error mapping explicit before UI derivations.

Target composition:

```text
build_request
-> execute_transport_effect
-> decode_response_schema
-> map_dto_to_domain
-> map_read_error_for_ui
```

Refactoring depth:

- Transport failures, invalid schema, outdated schema, and domain mapping failures are different typed errors.
- UI components no longer receive raw/partially decoded DTOs for covered read flows.
- Async/resource/cancellation concerns use selected TS library primitives rather than hand-managed Promise chains where covered.

Exit gates:

- Invalid RPC/schema response reaches UI as typed decode/mapping error.
- Existing dashboard valid-data rendering stays unchanged.

### Slice 5: TypeScript dashboard and graph view-model pipelines

**Goal**: move derived UI data out of components into typed, pure or effect-free pipeline stages.

Target composition:

```text
normalize_snapshots_or_history
-> compute_metrics
-> build_dashboard_aggregates
-> build_table_rows
-> build_treemap_nodes
-> build_timelapse_series
-> format_metrics
```

and:

```text
normalize_graph_snapshot
-> calculate_edge_labels
-> filter_sort_visible_edges
-> derive_detail_rows
-> calculate_viewport
```

Refactoring depth:

- React components become render shells over ready view models, typed loading state, or typed errors.
- Domain normalization and view-model derivation are directly testable outside React.

Exit gates:

- Dashboard and graph view-model tests cover success and invalid/empty/partial data.
- UI code no longer performs domain decoding or core aggregation logic inline.

### Slice 6: VS Code bridge adapters

**Goal**: make bridge lifecycle logic explicit without forcing VS Code APIs into pure FP.

Target composition:

```text
resolve_workspace_settings
-> build_cli_command
-> spawn_analysis_process_adapter
-> decode_progress_event_stream
-> start_rpc_datasource_adapter
-> handoff_webview_state
```

Refactoring depth:

- VS Code APIs and process objects remain shells.
- Progress JSON decode and bridge error mapping become typed stages.
- Cancellation is modeled as a typed bridge/orchestration outcome.

Exit gates:

- CLI spawn failure, malformed progress event, RPC startup failure, and cancellation each have typed bridge errors.
- Existing VS Code commands and build remain green.

### Slice 7: Cleanup and compatibility removal

**Goal**: remove temporary wrappers and enforce the new architecture.

Deliverables:

- Compatibility adapter inventory reviewed.
- Deprecated pipe helpers removed or isolated.
- Documentation completed.
- Tests cover the anti-cosmetic migration bar.

Exit gates:

- No covered primary process is just a top-level pipe over unchanged imperative internals.
- Remaining shells are intentional and documented.
- Stage-contract coverage target met.

## Testing Strategy

### Python

- Characterization tests for representative full analysis output.
- Stage-contract unit tests for validation, discovery, enrichment, provider, edge, export.
- Failure-path tests for invalid paths, malformed manifest, parse failure, unsupported AST model expression, Git/worktree failure.
- Property or table tests for pure reducers/resolvers where useful.
- Type checking with the existing `Expression`-based Python vocabulary after migration.

### TypeScript

- Unit tests for API/RPC response decode, DTO mapping, domain normalization, dashboard view-model, graph view-model.
- Typed error tests for transport, schema, mapping, partial data, cancellation.
- Component tests confirm components render supplied view models/errors rather than doing core derivation inline.
- Frontend build/typecheck remains green.

### VS Code

- Bridge adapter tests for settings resolution, command build, progress decoding, RPC startup error mapping, cancellation.
- Extension build/package remains green.

### Regression/Compatibility

- CLI commands continue to produce same outputs for valid inputs.
- JSON-RPC query shapes unchanged.
- Frontend screenshots/snapshots or DOM assertions unchanged for representative data.
- VS Code commands still work with same names/settings.

## Observability and Documentation

- Stage names become the canonical vocabulary for logs, progress, tests, and docs.
- Errors include stage name, safe input identity, underlying cause, category, and recovery/reporting intent.
- Docs include:
  - How to write a Python ROP stage.
  - How to wrap an imperative Python adapter.
  - How to write a TypeScript Effect/Either stage.
  - How to adapt React/VS Code/RPC boundaries.
  - Anti-patterns: top-level-only pipe, exception tunneling, nullable sentinel, framework leakage.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---:|---|
| Migration becomes cosmetic | High | Hardened spec, anti-cosmetic exit gates, shell inventory, stage-contract tests |
| Library adoption adds complexity | Medium | Reuse existing Python `Expression`; add only one TS library (`Effect`); keep adapters thin |
| Python ROP vocabulary forks | Medium | Do not add `returns`; wrap or alias `Expression` only |
| Effect too heavy for frontend team | Medium | Use Effect only where async/resource/errors matter; keep pure derivations as plain typed functions |
| Behavior changes during refactor | High | Characterization tests before each slice and representative output comparison |
| AST visitor refactor overreaches | Medium | Keep visitor as shell, extract only rules/facts/resolution into functions |
| VS Code lifecycle gets obscured | Medium | Keep VS Code APIs/process lifecycle imperative internally; wrap only boundaries |
| Implementation follows invented paths from old draft | High | Path guardrails in spec/tasks; T017-T019 inventory must record exact current files before edits |

## Milestones

1. Vocabulary and inventory.
2. Python Odoo analysis core.
3. Python enrichment subtree.
4. Python history/effect shell.
5. TypeScript API/RPC read pipeline.
6. TypeScript dashboard/graph view models.
7. VS Code bridge adapters.
8. Cleanup, docs, enforcement.

## Open Technical Questions

Resolved in `research.md`:

- Python library choice and mypy setup.
- TypeScript library choice.
- Error taxonomy granularity.
- Compatibility adapter lifecycle.
- Stage coverage threshold.
