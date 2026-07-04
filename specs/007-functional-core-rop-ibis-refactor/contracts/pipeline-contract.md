# Contract: Functional Pipeline, Typed Immutability, and Result Discipline

**Feature**: `007-functional-core-rop-ibis-refactor`

## Purpose

Define the internal contract for refactoring imperative workflows into functional, Railway-oriented pipelines.

## Stage Contract

A pipeline stage must behave as:

```text
Stage[Input, Output] = Input -> Result[Output, DomainError]
```

`Result` means the project's existing `Expression` result type. Success values
use `Ok(...)`; recoverable failures use `Error(DomainError)`. Project-local
code must not introduce alternative failure constructors; new migrated code
should use `Error(...)`.

Optional domain values must use `expression.Option`, with `Some(...)` for present
values and `Nothing` for absence. `None` is allowed only at external/public
boundary adapters and must be converted before domain pipeline stages.

Required properties:

- has a stable diagnostic name;
- declares whether it is pure or boundary/effectful;
- consumes explicit input only;
- returns `Ok(output)` on success;
- returns `Error(domain_error)` for recoverable failures;
- does not raise for ordinary recoverable domain/IO failures after boundary conversion;
- preserves unexpected programmer errors instead of hiding them as domain failures.

## Pure Stage Contract

A pure stage:

- does not read files, Git, environment variables, global mutable state, clocks, random values, or live database connections;
- does not mutate input objects;
- produces deterministic output for the same input;
- can be unit-tested without fixtures outside the input values.

## Boundary Stage Contract

A boundary stage:

- has an explicit `boundary_kind` such as `git`, `filesystem`, `duckdb`, `ibis_execution`, `server`, or `process`;
- catches known external exceptions and maps them to `DomainError`;
- records stage name, category, and causal message;
- preserves debug details for logs/debug mode where safe.


## Workflow Decomposition Contract

A migrated workflow must not remain a monolithic command/handler/analyzer function. It should be decomposed into named stages with these roles where applicable:

1. `validate_*`: pure validation from raw input to immutable params.
2. `load_context_*`: boundary acquisition for repo, filesystem, runtime, database, or Ibis backend.
3. `extract_*`: boundary or pure extraction stage, clearly tagged.
4. `normalize_*`: pure deterministic transformation.
5. `compute_*`: pure metric/domain computation.
6. `build_*_expr`: pure Ibis expression construction for relational reads.
7. `execute_*`: boundary execution stage.
8. `to_*_dto` / `render_*`: pure response shaping or rendering preparation.

A function that performs more than one of these roles should be split unless the implementation is trivial and documented as such.

## Result Discipline

Recoverable failures in migrated flows must use one consistent shape:

```text
Result[T, DomainError] = Ok[T] | Error[DomainError]
```

The following are prohibited in migrated recoverable paths:

- returning `None` to mean failure;
- returning partially shaped error dictionaries from domain code;
- swallowing exceptions and continuing with default values;
- mixing exception-based and result-based control flow inside the same stage chain;
- converting programmer bugs or violated invariants into misleading user errors.

## Composition Contract

Pipeline composition must short-circuit on `Error`:

```text
Ok(input) -> stage_a -> Ok(a) -> stage_b -> Ok(b)
Ok(input) -> stage_a -> Error(e) -> stage_b is not executed -> Error(e)
```

A composed workflow result must retain enough context to render a useful CLI/RPC/server error.

## Error Rendering Contract

Text mode:

```text
<readable message>
Hint: <optional action>
```

Machine-readable mode:

```json
{
  "ok": false,
  "error": {
    "code": "STABLE_ERROR_CODE",
    "message": "Readable message",
    "category": "query|git|filesystem|schema|lock|validation|runtime",
    "stage": "stage.name"
  }
}
```

Debug mode may include structured details or cause information. Default mode must not expose noisy stack traces for expected recoverable failures.

## Review Rules

- New non-trivial workflow code must be stage-composed.
- A function that both transforms domain data and performs IO should be split.
- Broad exception conversion must be justified and tested.
- Stage-level tests should cover both `Ok` and `Error` paths.


## Mandatory Type and Immutability Contract

Every production stage introduced or migrated by this feature must satisfy:

```text
stage_name(input: ImmutableInput) -> Result[ImmutableOutput, DomainError]
```

Allowed exceptions:

- total pure functions may return a typed immutable value directly when failure is impossible;
- adapter functions may call external libraries and catch their exceptions, but must return `Error(DomainError)` for expected failures;
- final renderers may return CLI/JSON/server output DTOs, but their inputs must already be typed.

Prohibited in migrated stages:

- untyped public stage signatures;
- `Any` for domain values unless documented as an interop boundary;
- `None` for optional domain values inside migrated core/query/pipeline stages;
- mutable stage-boundary DTOs;
- exception-driven recoverable flow;
- implicit reads from global config, clocks, environment, live DB connections, or singleton state.
