# Contract: ROP Pipeline Stage and Boundary Interfaces

**Spec ID**: `008-rop-pipeline-migration`  
**Date**: 2026-07-04

## Python Stage Contract

### Pure or validation stage

```text
StageName: Input -> Result[Output, TypedStageError]
```

Required properties:

- Function name matches the stage vocabulary.
- Stage target path is grounded in the current repository layout or explicitly introduced by a setup task.
- No hidden global dependencies.
- No framework objects in output.
- Exceptions are caught only when mapping a known domain/library failure into `TypedStageError`.
- Success and failure paths are tested directly.

### Effect adapter stage

```text
StageNameAdapter: Input -> Result[Output, TypedStageError]
AsyncStageNameAdapter: Input -> Awaitable[Result[Output, TypedStageError]]
```

Required properties:

- Performs exactly one effect category or closely related boundary operation.
- Adapter target path is grounded in the current repository layout or explicitly introduced by a setup task.
- Maps external exceptions/process failures to typed errors.
- Does not contain downstream business orchestration.
- Emits enough context for CLI/progress/UI reporting.

## TypeScript Stage Contract

### Pure derivation/decode stage

```text
StageName: (input: Input) => Either<TypedStageError, Output>
```

or, when failure is impossible:

```text
StageName: (input: Input) => Output
```

Required properties:

- UI components do not perform this core derivation inline.
- Frontend target path uses current repository folders such as `frontend/src/api`, `frontend/src/transforms`, `frontend/src/pages`, or `frontend/src/components` unless inventory records a reorganization.
- DTO/schema/domain errors are distinguishable.
- Outputs are ready for the next pipeline stage or for rendering.

### Effectful read/bridge stage

```text
StageName: (input: Input) => Effect<Output, TypedStageError, Context>
```

Required properties:

- Async, resource, cancellation, transport, and context requirements are tracked by the selected library vocabulary.
- VS Code target path uses current `vscode-extension/src` bridge/command files recorded in inventory before edits.
- Raw thrown exceptions and rejected promises are captured and mapped.
- UI/VS Code receives typed displayable errors, not raw unknown exceptions.

## Boundary Contract

All boundaries from old imperative/object code into the railway must provide:

- Adapter name.
- Concrete target path and exact current entrypoint path when wrapping old code.
- Wrapped operation.
- Input type.
- Output type.
- Error mapping.
- Reason the operation remains a shell.
- Tests for success and mapped failure.

## Compatibility Adapter Naming Convention

- **Python**: `<original_function>_compat` or `<module>_compat` in `src/ppi/core/compat.py` or sibling `compat.py` files.
- **TypeScript**: `<originalFunction>Compat` in a `compat.ts` module adjacent to the new pipeline.
- **VS Code Bridge**: `<operation>Compat` in `vscode-extension/src/bridge/compat.ts`.
- Each adapter must have a single clear replacement target stage and an `allowed_until_slice` field in the inventory.

## Compatibility Adapter Removal Policy

1. No compatibility adapter may remain indefinitely. Each must have a removal or reclassification task in the Slice 7 cleanup.
2. Adapters that were only needed for one slice (temporary wrappers) are removed in that slice's cleanup subtask.
3. Adapters with no remaining callers after all slices must be deleted; leftover import references must be updated.
4. An adapter may be deferred past Slice 7 only with an explicit architecture decision record in `.specify/memory/constitution.md`.

## Path-Change Policy

1. No pipeline file or function may be moved to a new path before the inventory records the old canonical path.
2. Path changes without inventory entries are treated as spec violations.
3. If the repository is reorganized during this feature (e.g. `src/ppi/core` to `src/ppi/analysis`), the inventory must record the decision before any code moves.

## Stage Contract Checklist

## How to Write a New Python Stage (FR-015)

1. Pick a name matching the domain vocabulary (e.g. `resolve_addons_paths`, `enrich_modules_with_code_analysis`).
2. Define input and output types — prefer plain dataclasses or tuples; no framework objects.
3. Return `Result[Output, TypedStageError]` from `expression.core.result`.
4. If the stage can fail with a domain error, use one of the five `TypedStageError` variants from `ppi.rop.errors`.
5. If the stage performs IO (filesystem, process, git), wrap it as an effect adapter in `src/ppi/adapters/`.
6. Add a direct test for the success path and one for each failure variant.
7. Register the stage in the pipeline's composition function (e.g. `odoo_project_analysis_pipeline`).

**Example — pure stage:**

```python
from expression.core.result import Ok, Result
from ppi.rop.errors import ValidationFailure
from ppi.rop.types import StageResult

def validate_version_stage(version_str: str) -> StageResult[str]:
    parts = version_str.split(".")
    if len(parts) != 3:
        return Error(ValidationFailure(
            stage="validate_version",
            message=f"Expected semver, got {version_str!r}",
            safe_input_id=version_str,
        ))
    return Ok(version_str)
```

**Example — effect adapter:**

```python
from expression.core.result import Error, Ok
from ppi.rop.adapters import exception_to_error
from ppi.rop.types import StageResult

def read_file_adapter(path: Path) -> StageResult[str]:
    try:
        return Ok(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return Error(exception_to_error(exc, stage="read_file"))
```

## How to Write a New TypeScript Stage (FR-015)

1. Add the stage function to the appropriate module under `frontend/src/api/`, `frontend/src/transforms/`, or `vscode-extension/src/bridge/`.
2. Use `Effect.Effect<Output, PipelineError>` for async/effectful stages; plain function signature for pure derivation.
3. Return typed `PipelineError` using `pipelineError()` or `bridgeFailure()` helpers.
4. Add a test in the adjacent `.test.ts` file covering success, each failure category, and edge cases.

**Example — pure derivation:**

```typescript
import type { PipelineError } from "../rop/types";
import { pipelineError } from "../rop/effect";

export function computeAggregate(
  values: readonly number[],
): number {
  return values.reduce((a, b) => a + b, 0) / values.length;
}
```

**Example — effectful stage:**

```typescript
import { Effect } from "effect";
import type { PipelineError } from "../rop/types";
import { pipelineError } from "../rop/effect";

export function fetchData(url: string): Effect.Effect<string, PipelineError> {
  return Effect.tryPromise({
    try: () => fetch(url).then((r) => r.text()),
    catch: (error) => pipelineError("transport", "fetchData", String(error)),
  });
}
```

## How to Adapt an Imperative Function (FR-015)

1. Identify the imperative function you need to call from a pipeline.
2. Create an adapter function with a typed signature matching the pipeline's input/output contract.
3. Wrap the imperative call in a try/except (Python) or Effect.tryPromise (TypeScript).
4. Map exceptions to `TypedStageError` / `PipelineError` / `BridgeFailure`.
5. Place the adapter in the appropriate `adapters/` or adjacent module.
6. Name it with a `_adapter` / `Adapter` suffix.

**Python adapter pattern:**

```python
def legacy_operation_adapter(input: InputType) -> StageResult[OutputType]:
    try:
        return Ok(legacy_imperative_function(input))
    except SpecificError as exc:
        return Error(ValidationFailure(stage="legacy_operation", message=str(exc), safe_input_id=str(input)))
```

**TypeScript adapter pattern:**

```typescript
export function legacyOperationAdapter(input: InputType): Effect.Effect<OutputType, PipelineError> {
  return Effect.tryPromise({
    try: () => legacyImperativeFunction(input),
    catch: (error) => pipelineError("domain", "legacyOperationAdapter", String(error)),
  });
}
```

## How to Map Errors (FR-015)

1. At pipeline boundaries (CLI, RPC, UI, VS Code), map typed errors to interface-specific representations.
2. Use a dedicated mapping function (e.g. `_map_validation_to_analysis_error`, `mapReadErrorForUi`).
3. Preserve the original typed error's context (stage, message, cause).
4. Test each mapped output for the expected shape.

**Python boundary mapping:**

```python
def _map_to_ui_error(err: TypedStageError) -> str:
    match err:
        case ValidationFailure() as v: return f"Validation: {v.message}"
        case OrchestrationFailure() as o: return f"Orchestration: {o.message}"
        case _: return str(err)
```

**TypeScript boundary mapping:**

```typescript
export function mapBridgeErrorForUi(error: BridgeFailure): string {
  return `[${error.category}] ${error.stage}: ${error.message}`;
}
```

## Stage Contract Checklist

All pipeline stages must satisfy these checks before being considered migrated:

| Check | Criterion |
|---|---|
| NamedStage | stage has a stable name matching domain vocabulary |
| TypedContract | input/output/error types are explicit |
| TestedSuccess | success path has a direct test |
| TestedFailure | failure path has a direct test (if stage can fail) |
| NoHiddenIO | no inline filesystem/network/process calls |
| NoFrameworkLeak | no AST/React/VS Code objects in stage output |
| PathGrounded | target path is in the current repository layout |
| AdapterNamed | effect adapter has a `_adapter` or `Adapter` suffix |
| CompatNamed | compatibility adapter has a `_compat` or `Compat` suffix |

## Completion Contract

A pipeline is complete only when:

1. Its ordered target stage list exists.
2. Stages compose with selected library primitives.
3. Failure path is typed and tested.
4. Remaining shells are inventoried.
5. Compatibility adapters are removed or explicitly deferred.
6. Target paths are grounded in the current repository layout and exact old entrypoints are recorded in inventory.
7. No cosmetic top-level pipe wrapper hides unchanged imperative internals.
8. All stage contract checklist items pass for every stage in the pipeline.
