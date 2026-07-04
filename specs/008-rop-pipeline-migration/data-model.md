# Data Model: Railway Oriented Pipeline Migration

**Spec ID**: `008-rop-pipeline-migration`  
**Date**: 2026-07-04

This feature does not introduce new persisted product data. The model below describes architectural entities and contracts used to plan and validate the refactor.

## Entity: PipelineStage

Represents one named transformation in a railway.

Fields:

- `name`: stable stage name aligned with domain vocabulary.
- `family`: backend-analysis, backend-history, frontend-read, frontend-viewmodel, vscode-bridge.
- `kind`: pure, effect-adapter, framework-adapter, compatibility-adapter.
- `input_type`: typed input state or value.
- `success_type`: typed success output.
- `failure_type`: typed failure output when stage can fail.
- `recoverability`: success-only, recoverable-domain, short-circuit, mixed.
- `dependencies`: explicit context/config/services required by the stage.
- `tests`: success, failure, adapter, characterization coverage references.
- `target_path`: concrete repository file or directory where the stage will live.

Validation:

- Covered major stages must have non-empty `name`, `input_type`, `success_type`, `kind`, and path-grounded `target_path`.
- Failing stages must define `failure_type`.
- Compatibility adapters must have a removal or replacement target.

## Entity: PipelineState

Represents the immutable/replacement-based value passed between stages.

Fields:

- `config`: validated configuration required by downstream stages.
- `artifacts`: analysis modules, metrics, AST facts, provider maps, edges, scores, failures.
- `context`: explicit dependencies or environment handles when the selected library supports context.
- `stage_trace`: optional diagnostic trace of stage outcomes.

Validation:

- Core stages must not mutate shared state in place across stage boundaries.
- Object/framework handles may exist only inside context or adapter shells, not as hidden globals.

## Entity: TypedStageError

Represents structured failure in the railway.

Fields:

- `category`: ValidationFailure, RecoverableDomainFailure, OrchestrationFailure, DecodeMappingFailure, BridgeFailure.
- `stage`: stage where failure originated or was mapped.
- `safe_input_id`: path/module/commit/request identity where safe to expose.
- `message`: developer-readable message.
- `cause`: underlying exception/error if available and safe.
- `recovery_intent`: abort, skip-and-report, retry, show-to-user, log-only.
- `details`: structured details such as path, module name, commit hash, schema path, RPC method.

Validation:

- Errors crossing CLI/RPC/TS/UI/VS Code boundaries must be mapped to boundary-safe variants.
- Recoverable domain failures must not be represented only as thrown exceptions.

## Entity: EffectShell

Represents a boundary around IO/framework/lifecycle/object behavior.

Fields:

- `name`: shell name.
- `runtime`: Python CLI, Python storage/query, frontend browser, VS Code extension.
- `operation`: filesystem, Git, subprocess, RPC, HTTP, storage, AST visitor, React render, VS Code API.
- `adapter_name`: function-shaped adapter used by pipeline stages.
- `target_path`: concrete repository file or directory where the adapter will live.
- `error_mapping`: typed error constructor or mapper.
- `reason_kept_imperative`: why this remains outside the core pure/ROP stage.

Validation:

- Every shell inside covered flows must have an adapter name and path-grounded target path.
- Shell objects must not leak into pure stage outputs.

## Entity: CompatibilityAdapter

Represents a temporary wrapper around old imperative internals during incremental migration.

Fields:

- `name`: adapter function name.
- `wrapped_function`: old function or module being wrapped.
- `target_stage`: eventual proper stage replacement.
- `allowed_until_slice`: migration slice by which it should be removed or reclassified.
- `tests`: behavior-preserving tests.

Validation:

- Compatibility adapters cannot be used to mark a pipeline fully migrated.
- Each compatibility adapter must be reviewed in Slice 7 cleanup.

## Entity: PipelineInventory

Represents the complete coverage map.

Fields:

- `pipeline_name`: stable pipeline name.
- `parent_pipeline`: optional parent.
- `child_pipelines`: nested pipelines.
- `current_entrypoints`: current functions/components/commands, including exact current file paths discovered before editing.
- `target_stages`: ordered stage list with concrete target path for each stage.
- `remaining_shells`: allowed effect/framework shells.
- `completion_status`: not-started, compatibility-wrapped, partially-migrated, migrated, cleaned-up.

Validation:

- A pipeline cannot be `migrated` if any target stage is missing tests or path-grounded inventory entry.
- A pipeline cannot be `cleaned-up` if compatibility adapters remain without justification.
