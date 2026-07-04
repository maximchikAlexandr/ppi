# Data Model: Spec 007 — Typed Immutable Pipeline and Ibis Query Models

**Feature**: `007-functional-core-rop-ibis-refactor`

This data model describes architectural/domain entities introduced or standardized by the refactor. It does not replace the existing DuckDB schema; storage schema compatibility remains a requirement.

## Entity: Result

Represents the outcome of a pipeline stage or boundary operation. The canonical
runtime representation is `expression.Result`; `src/ppi/core/result.py` may
re-export `Result`, `Ok`, and `Error`, but must not define an incompatible
second result type.

| Field | Type | Required | Notes |
|---|---|---:|---|
| `kind` | `ok | error` | Yes | Conceptual discriminator for docs/tests; runtime uses `Expression` `Ok`/`Error` |
| `value` | generic | Only for ok | Immutable success payload |
| `error` | `DomainError` | Only for error | Typed failure payload |

**Validation rules**:

- Exactly one of `value` or `error` is present.
- `Ok` values should be immutable or treated as immutable across stage boundaries.
- `Error` must contain a stable error code and stage context where available.

**State transitions**:

- `Ok[A] -> bind(stage) -> Ok[B]` when stage succeeds.
- `Ok[A] -> bind(stage) -> Error[E]` when stage fails.
- `Error[E] -> bind(stage) -> Error[E]` without executing dependent stage.

## Entity: DomainError

Recoverable failure used by CLI, pipeline, query, and server adapters.

| Field | Type | Required | Notes |
|---|---|---:|---|
| `code` | enum/string | Yes | Stable machine-readable code |
| `category` | enum | Yes | Example: validation, git, filesystem, schema, lock, query, runtime |
| `message` | string | Yes | User-readable message |
| `stage` | string | Recommended | Pipeline stage that produced the failure |
| `details` | immutable mapping | Optional | Safe structured context |
| `cause` | exception/ref | Optional | Preserved for debug/logging, not always rendered |

**Validation rules**:

- User-facing messages must not require stack traces to be useful.
- Machine-readable modes must include `code` and `message`.
- Programmer errors should not be silently converted to misleading `DomainError` values.

## Entity: Option

Represents an optional domain value inside migrated core, pipeline, query, and
DTO-mapping internals. The canonical runtime representation is
`expression.Option`; `Some(value)` means present and `Nothing` means absent.

**Validation rules**:

- `None` is not a domain-stage absence protocol.
- Boundary adapters convert public `null`, missing CLI values, Pydantic `None`,
  or external-library `None` into `Option` before domain processing.
- Domain stages convert `Option` back to public `None` only at serializer or
  response-contract boundaries where null is already part of the public shape.

## Entity: PipelineStage

Named transformation or boundary step.

| Field | Type | Required | Notes |
|---|---|---:|---|
| `name` | string | Yes | Stable diagnostic stage name |
| `input_type` | type/ref | Yes | Expected immutable input shape |
| `output_type` | type/ref | Yes | Success output shape |
| `boundary_kind` | enum | Yes | `pure`, `git`, `filesystem`, `duckdb`, `ibis_execution`, `server`, etc. |
| `function` | callable | Yes | Returns `Result[output_type, DomainError]` |

**Validation rules**:

- Pure stages do not perform IO, read globals, mutate inputs, or execute database queries.
- Boundary stages convert known external failures into `DomainError`.
- Stage names appear in diagnostics and tests.

## Entity: Immutable Domain Model

Represents commit, file, metric, run, query parameter, and response-intermediate data passed between stages.

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` / natural key | string/int/tuple | Contextual | Only when the domain object has identity |
| domain fields | scalar/tuple/frozen mapping | Yes | Depends on existing PPI models |
| `created_from` | optional metadata | Optional | Useful for diagnostics or fixture provenance |

**Validation rules**:

- No shared mutable lists/dicts cross stage boundaries.
- Large tabular data should remain lazy/relational where possible instead of being copied into immutable Python collections prematurely.

## Entity: IbisQueryExpression

Backend-evaluable relational query description.

| Field | Type | Required | Notes |
|---|---|---:|---|
| `query_name` | string | Yes | Stable query family identifier |
| `expression` | Ibis expression | Yes | Lazy expression built from bound tables |
| `expected_schema` | schema/ref | Recommended | Used by tests and contract validation |
| `parameters` | immutable model | Optional | Validated query parameters |
| `ordering_contract` | enum/list | Optional | Defines guaranteed ordering, if any |

**Validation rules**:

- Expression builders do not execute queries.
- Expression output schema matches public response mapping requirements.
- Query parameters are validated before expression construction.

## Entity: DuckDBBoundaryOperation

Approved direct DuckDB operation.

| Field | Type | Required | Notes |
|---|---|---:|---|
| `operation_name` | string | Yes | Stable identifier |
| `category` | enum | Yes | connection, schema, migration, lock, transaction, write, pragma, unsupported_feature |
| `module` | path | Yes | Location of direct DuckDB usage |
| `reason` | string | Yes | Why Ibis is not used here |
| `test_coverage` | list/ref | Yes | Tests that cover it |
| `review_status` | enum | Yes | approved, temporary, revisit_by |

**Validation rules**:

- Analytical read/query operations cannot be permanent boundary operations without a concrete exception reason.
- Every boundary operation appears in the migration inventory.

## Entity: MigrationInventoryEntry

Tracking record for direct DuckDB/SQL usage and migration status.

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | string | Yes | Example: `MI-001` |
| `module` | path | Yes | Source file path |
| `symbol` | function/class/ref | Recommended | Code location |
| `usage_type` | enum | Yes | read_query, analytics, write, schema, transaction, lock, maintenance, test_fixture, false_positive |
| `current_pattern` | string | Yes | Example: raw SQL string, duckdb connection execute, query helper |
| `target_pattern` | enum | Yes | ibis_expression, duckdb_boundary, remove, no_change_false_positive |
| `status` | enum | Yes | discovered, in_progress, migrated, approved_exception, removed |
| `reason` | string | Conditional | Required for exceptions |
| `owner` | string | Recommended | Responsible maintainer/area |
| `tests` | list/ref | Yes | Golden/contract/unit tests |
| `notes` | string | Optional | Caveats or performance notes |

**Validation rules**:

- All direct SQL/DuckDB findings must have an entry.
- `approved_exception` requires a reason and tests.
- `read_query` and `analytics` default target is `ibis_expression`.

## Entity: PublicResponseContract

Stable output shape consumed by CLI JSON mode, query commands, RPC, server/dashboard, and VS Code bridge.

| Field | Type | Required | Notes |
|---|---|---:|---|
| `surface` | enum | Yes | cli_text, cli_json, query, rpc, dashboard |
| `name` | string | Yes | Command/endpoint/query family |
| `fields` | schema/ref | Yes | Public fields and types |
| `ordering` | rule | Optional | Ordering guarantees if currently defined |
| `error_shape` | schema/ref | Required for machine modes | Stable error code/message mapping |
| `compatibility_tests` | list/ref | Yes | Tests proving compatibility |

**Validation rules**:

- Public field names and null semantics must remain compatible unless a migration note exists.
- Refactoring cannot expose internal Ibis/DuckDB details in public output.


## Typed Immutability Rules

- Every cross-stage domain value MUST have an explicit type and immutable runtime representation.
- Prefer frozen dataclasses or equivalent frozen models for domain entities and tuples/frozen containers for collections.
- `dict[str, Any]` and mutable `list` values are allowed only at serialization/parsing boundaries and must be converted into typed immutable structures before pipeline processing.
- Ibis query parameters MUST be typed immutable value objects.
- Public DTOs may use `TypedDict` or serializer models, but mutation must not be visible to domain stages.
- Any boundary-local mutation for performance must be hidden behind a pure interface and documented in the migration inventory or review checklist.
