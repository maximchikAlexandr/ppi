# Implementation Plan: Spec 007 — Functional Core, ROP, Typed Immutable Data & Ibis-First Refactor

**Feature**: `007-functional-core-rop-ibis-refactor`  
**Spec**: `specs/007-functional-core-rop-ibis-refactor/spec.md`  
**Created**: 2026-07-03  
**Phase**: plan  
**Ambition**: maximum practical migration to functional pipelines, result-based error handling, immutable domain data, and Ibis-first relational access.

## Summary

Refactor PPI's Python backend so that product behavior remains compatible while internal workflows become explicit functional pipelines. The project keeps DuckDB as the local persistence engine for `.ppi/history.duckdb`, but Python read/query/analytical transformations must move to Ibis expressions by default. Raw analytical SQL is treated as technical debt and must either be migrated, isolated as an approved DuckDB boundary, or documented as a temporary exception with owner, reason, and tests.

The architecture will separate pure domain transformations from effectful boundaries:

1. CLI/RPC/server adapters parse input and render output.
2. Orchestrators compose typed pipeline stages.
3. Pipeline stages consume immutable input values and return `Result[Value, DomainError]`.
4. Query/read-model stages build Ibis expressions, execute them through a backend adapter, and map results into public contracts.
5. DuckDB-specific operations are restricted to connection lifecycle, schema/migration, locking, transaction/write mechanics, pragmas, and proven unsupported Ibis cases.


## Precision Audit: Ambition Tightening

This plan is intentionally **not** a cosmetic cleanup plan. It is a codebase-level architectural refactor with measurable migration pressure. The target state is:

1. **Functional pipeline as the default shape** for every non-trivial Python workflow touching analysis, history ingestion, storage read-models, query/RPC/dashboard data preparation, and CLI/server orchestration.
2. **Ibis as the default relational language** for all read/query/analytical transformations over DuckDB-backed history data.
3. **Raw SQL as an exception**, not a style choice. Every remaining raw SQL string or direct DuckDB call must be either removed, moved into an approved boundary, or listed in the migration inventory with evidence.
4. **Railway Oriented Programming as the normal failure model** for recoverable failures: no ad-hoc `None`, sentinel dicts, broad swallowed exceptions, or mixed exception/result paths in migrated workflows.
5. **Immutability at stage boundaries**: mutable implementation details may exist locally inside a stage, but public stage inputs/outputs and domain DTOs must be immutable or treated as immutable.

### Anti-Laziness Gates

The implementation is considered insufficient if any of the following are true after a migration slice:

- A read/query/dashboard/RPC path still builds `SELECT`, `WITH`, `JOIN`, `GROUP BY`, `ORDER BY`, or aggregate SQL strings outside the approved DuckDB boundary.
- A migrated workflow remains a long imperative function with interleaved validation, IO, transformation, database calls, and rendering.
- Recoverable errors are represented sometimes by exceptions, sometimes by `None`, sometimes by dicts, and sometimes by `Result` in the same flow.
- Stage functions accept or mutate shared global state, live database connections, environment variables, or clocks without being marked as boundary stages.
- Ibis is used only as a thin wrapper while business logic still lives in raw SQL strings.

### Strict Target Metrics

| Metric | Target | Evidence |
|---|---:|---|
| Discovered read/query/analytics raw SQL migrated to Ibis | 100% unless approved exception | migration inventory + golden tests |
| Direct DuckDB usage outside approved boundary/test modules | 0 | guardrail script |
| Non-trivial migrated workflows expressed as named pipeline stages | 100% for touched area | architecture tests + code review checklist |
| Recoverable failures in migrated workflows using `Result` | 100% for touched area | unit/error injection tests |
| Mutable cross-stage domain DTOs in migrated workflows | 0 | type/model review + tests |
| Query families with legacy-vs-Ibis golden comparison before removal | 100% | golden test report |


## Strict Functional Programming Acceptance Gates

This plan intentionally targets a maximal practical FP migration, not a light refactor. A migrated area is not accepted unless all gates below pass:

- Public stage, model, Result, Option, error, Ibis builder, and mapper interfaces are explicitly typed.
- Data crossing stage boundaries is immutable; mutable inputs from CLI/JSON/DB are normalized before entering the core.
- Pure functions contain no IO, logging, connection usage, global reads, clock access, environment access, or hidden mutation.
- Recoverable failures return `Error(DomainError)` and compose through `bind`/pipeline short-circuiting.
- Exceptions from DuckDB/Ibis/Git/filesystem are converted only at adapter/boundary stages.
- Ibis builders produce lazy expressions and do not execute, materialize, or generate raw SQL strings.
- No migrated read/query/analytics code builds `SELECT`, `WITH`, `JOIN`, `GROUP BY`, `ORDER BY`, or aggregate SQL text outside an approved boundary.
- Static typing, architecture tests, and golden tests are part of the definition of done, not optional polish.


## Complete Ambition Controls

The plan is complete only when these controls are treated as first-class implementation constraints, not historical notes:

1. **Surface-complete query inventory**: query-family inventory must cover documented CLI `query` metrics, RPC methods, dashboard/server datasets, VS Code bridge reads, history read models, and any helper that exposes database-shaped data. Unknown status is not allowed after Phase 2.
2. **Complete DuckDB interaction disposition**: the inventory must cover reads, analytics, writes, ingestion, bulk load/export, schema/migrations, locks, transactions, maintenance, test fixtures, and false positives. Ibis/backend abstraction is preferred wherever it can preserve compatibility and transactional semantics; direct DuckDB is allowed only as a named boundary exception.
3. **Vertical-slice obligation**: MVP and final delivery must prove at least one real end-to-end slice across Ibis query migration and functional pipeline migration, then continue by named query/workflow family until every P1 surface has a disposition.
4. **Executable evidence over prose**: final acceptance depends on guardrail commands, golden-output reports, type-check output, inventory validation, and architecture-review pass/fail evidence; documentation alone cannot satisfy the strict FP/Ibis gates.

## Technical Context

**Language/runtime**: Python project with CLI, server/dashboard and RPC-oriented paths.  
**Primary package areas**: `src/ppi/adapters`, `src/ppi/cli`, `src/ppi/core`, `src/ppi/history`, `src/ppi/query`, `src/ppi/runtime`, `src/ppi/server`, `src/ppi/storage`.  
**Existing storage**: local DuckDB history store under `.ppi/history.duckdb`.  
**Target relational abstraction**: Ibis expressions/functions executed against DuckDB backend.  
**Compatibility surfaces**: CLI commands `doctor`, `analyze`, `query`, `serve`, `rpc`; dashboard and VS Code/RPC response shapes; existing history stores.  
**Testing baseline**: existing automated tests plus golden-output tests for query migration, architecture guardrail tests, error-injection tests, and smoke/performance scenarios.

## Constitution Check

Project constitution exists at `.specify/memory/constitution.md` and is applicable.
Spec 007 directly targets the constitution's functional core, layered core
independence, typed contracts, explicit error handling, plugin/fact-contract
extensibility, and single-writer DuckDB ownership principles. Result: **PASS**.
No constitution violations are blocking this plan; remaining risks are tracked as
architecture guardrails, migration inventory requirements, and final architecture
review evidence.

## Architecture Principles

### AP-001: Functional core, imperative shell

Domain calculations, normalization, aggregation, filtering, and response shaping must live in pure functions where practical. IO, clock access, environment access, filesystem, Git, DuckDB/Ibis execution, locks, and process/server concerns must be isolated at named boundary modules.

### AP-002: Pipeline-first orchestration

Non-trivial workflows must be represented as named pipeline stages with explicit input/output contracts. The default orchestration style is composition of stages, not nested imperative procedures. At minimum this applies to:

- repository discovery and validation;
- Git/history extraction;
- metric calculation;
- history ingestion/write preparation;
- read-model/query construction;
- dashboard/RPC response preparation;
- CLI output rendering.

### AP-003: Result-based recoverable failures

Recoverable failures use typed result values. Exceptions remain appropriate for programmer errors, invariant violations, and truly unexpected failures. Boundary adapters catch known external exceptions and convert them into domain errors with stable error codes.

### AP-004: Immutable domain data by default

Data passed between stages uses frozen dataclasses, immutable mappings/sequences, tuples, or equivalent immutable models. Mutable data structures are permitted as short-lived implementation details inside a stage or boundary but cannot leak across stage boundaries.

### AP-005: Ibis-first read/query/analytics

Every analytical read/query transformation must be expressed with Ibis table/expression/function composition unless the migration inventory approves an exception. DuckDB remains the execution/storage backend, not the everyday query language used by business logic.

### AP-006: DuckDB boundary is narrow and named

The only acceptable long-term direct DuckDB usage categories are:

- connection open/close and backend binding;
- database file management;
- schema initialization and migrations;
- locking and transaction control;
- pragmas and maintenance commands;
- write/bulk mechanics not safely expressible through Ibis;
- a measured or documented unsupported Ibis feature.

## Proposed Module Shape

The exact filenames can change during implementation, but the plan should converge on these responsibilities.

```text
src/ppi/
  core/
    result.py              # Expression Result/Ok/Error and Option/Some/Nothing re-exports plus combinators and error mapping helpers
    errors.py              # DomainError, ErrorCode, stage context
    pipeline.py            # Stage protocol, compose/bind/tap/recover helpers
    immutable.py           # immutable collection helpers, validation utilities
  history/
    pipeline.py            # analyze/history ingestion pipeline composition
    stages.py              # pure or boundary-tagged stages
    models.py              # frozen domain models for commits/files/metrics/runs
  storage/
    duckdb_boundary.py     # allowed direct DuckDB connection/schema/lock/write boundary
    ibis_backend.py        # Ibis connection factory, table bindings, execution helpers
    ibis_queries.py        # Ibis expression builders for read/query/read-model paths
    inventory.py           # migration inventory definitions/reporting
  query/
    read_models.py         # pure mapping from Ibis query results to public DTOs
    pipeline.py            # request -> validated params -> Ibis expr -> result DTO
    contracts.py           # stable public result models retained/backward compatible
  cli/
    render_errors.py       # DomainError -> text/json rendering
    commands/...           # adapters only; no business SQL or hidden orchestration
  server/
    handlers/...           # adapters only; invoke query pipelines and render contracts
```


## Refactoring Map by Python Area

| Area | Current risk to eliminate | Target refactor | Ibis expectation | ROP / functional expectation |
|---|---|---|---|---|
| `src/ppi/cli` | Commands orchestrate too much or render DB/domain errors directly | Thin adapters: parse args, invoke pipeline, render `Result` | No raw SQL; no direct DuckDB | Convert command outcomes through `Result` renderers |
| `src/ppi/server` | Handlers may mix request parsing, DB reads, DTO shaping | Thin HTTP/RPC adapters over query pipelines | No raw SQL in handlers | Handlers receive `Ok(dto)` or `Error(error)` |
| `src/ppi/query` | Query families may encode DuckDB SQL directly | Validated params -> Ibis expr builder -> execution boundary -> DTO mapper | Mandatory Ibis-first | Params/results immutable; invalid input returns `Error` |
| `src/ppi/history` | Analysis/history ingestion may be imperative and side-effectful | Named extraction/normalization/metric/write-prep stages | Reads/aggregates over history via Ibis where relational | Stage-by-stage `Result` composition |
| `src/ppi/storage` | DuckDB calls spread across business modules | `duckdb_boundary.py` + `ibis_backend.py` + `ibis_queries.py` | Ibis builders for reads; DuckDB only for allowed boundary | Boundary exceptions mapped to `DomainError` |
| `src/ppi/core` | Shared logic may be mutable or exception-heavy | Pure functions, frozen models, result/pipeline primitives | No database access | Foundation for `Result`, `DomainError`, stage composition |
| `src/ppi/runtime` | Runtime state can leak into domain logic | Explicit runtime context passed to boundary stages only | No query logic | Runtime errors mapped once at boundary |
| Tests | Tests may only check happy path | Golden, error-injection, architecture guardrails | Legacy-vs-Ibis comparison | `Ok` and `Error` path coverage |

## Boundary Classification

| Area | Desired end state | Direct DuckDB allowed? | Ibis expected? |
|---|---|---:|---:|
| Schema creation/migrations | Explicit boundary functions | Yes | No |
| Connection lifecycle | Boundary-only | Yes | Backend binding only |
| Locking/transactions | Boundary-only | Yes | No |
| Bulk inserts/history writes | Boundary-only unless Ibis is safe | Yes, documented | Maybe |
| Read queries for CLI/query/RPC/dashboard | Ibis expression builders | Only approved exceptions | Yes |
| Analytical aggregates/window/filter/project operations | Ibis expression builders | No by default | Yes |
| DTO/JSON shaping | Pure functions over result data | No | No, unless still relational |
| Error rendering | Pure mapping | No | No |

## Phase 0 Research Summary

See `research.md` for decisions and alternatives. Key plan decisions:

- Use the existing `Expression` `Result`, `Ok`, and `Error` primitives as the canonical recoverable-failure representation, and `Option`, `Some`, and `Nothing` as the canonical domain-absence representation; keep any in-repo `result.py` layer limited to aliases, combinators, and PPI-specific helpers.
- Use Ibis expression builders as pure query-description functions and isolate expression execution in a backend/boundary module.
- Keep DuckDB writes and schema mechanics behind a narrow boundary in the first migration wave.
- Require an automated inventory/report for direct SQL/DuckDB usage before broad refactoring.

## Phase 1 Design Summary

Design artifacts produced:

- `data-model.md`: domain and planning entities for pipelines, result errors, Ibis expressions, migration inventory, and boundary exceptions.
- `contracts/pipeline-contract.md`: stage and result contracts for functional pipeline composition.
- `contracts/data-access-contract.md`: Ibis-first data-access boundary and DuckDB exception contract.
- `contracts/public-behavior-contract.md`: public compatibility contract for CLI/RPC/dashboard behavior.
- `quickstart.md`: validation workflow for contributors implementing the refactor.

## Migration Strategy

### Wave 0: Inventory and guardrails

- Scan Python files for `duckdb`, `.execute(`, `.sql(`, SQL keywords in string literals, and database-shaped helpers.
- Classify every finding into `read_query`, `analytics`, `write`, `ingestion`, `bulk_import_export`, `schema`, `migration`, `transaction`, `lock`, `maintenance`, `test_fixture`, or `false_positive`.
- Create `migration_inventory` records with owner, status, reason, test coverage, target migration path, approved boundary category if non-Ibis, and future re-evaluation condition.
- Add guardrail tests or lint scripts that fail on new raw analytical SQL outside approved boundary modules.


### Wave 0.5: Query-family inventory with mandatory disposition

Before replacing code, produce a query-family inventory, not only a grep list. Each family must have:

- public caller surface: CLI metric, RPC method, dashboard tab, server endpoint, or internal history consumer;
- current implementation symbols/modules;
- source tables/views used;
- output contract and ordering/null/type guarantees;
- migration decision: `ibis_migrate`, `duckdb_boundary`, `remove_dead_code`, or `test_fixture`;
- golden fixture coverage;
- removal condition for legacy SQL.

No query family may be marked complete while its legacy raw SQL remains callable in the normal path.

### Wave 0.6: Non-query DuckDB disposition

All non-query DuckDB interactions must also be dispositioned before final delivery. Write, ingestion, bulk import/export, schema/migration, lock, transaction, and maintenance paths must be evaluated for safe expression through the Ibis/backend abstraction. When direct DuckDB remains the correct tool, the implementation must keep it behind `duckdb_boundary`, attach tests for the boundary semantics, and record a re-evaluation condition in the migration inventory.

### Wave 2.5: Remove dual-path query code

After a query family has Ibis golden parity, remove or disable the normal legacy SQL path. Keeping both paths permanently is a failure mode because it normalizes two query languages and doubles maintenance. A temporary feature flag is allowed only with an expiry decision in the migration inventory.

### Wave 3.5: Convert orchestration hotspots, not just leaf helpers

Functional refactoring must reach orchestration hotspots. It is not enough to wrap leaf functions. Long command/handler/analyzer flows must be split into:

1. input validation stage;
2. context/boundary acquisition stage;
3. pure transformation stages;
4. Ibis expression construction stage for relational reads;
5. execution/write boundary stage;
6. pure response/DTO/render preparation stage.

### Wave 1: Foundation abstractions

- Introduce `Result`, `DomainError`, pipeline combinators, stage protocol, and immutable data conventions.
- Convert top-level error rendering to understand typed result failures in text, JSON, and RPC modes.
- Add architecture tests proving core/pipeline modules do not import boundary modules directly except through approved interfaces.

### Wave 2: Ibis backend and read query migration

- Add Ibis DuckDB backend connection/binding layer.
- Build Ibis expression factories for existing read/query/dashboard/RPC query families.
- For each query family, run golden tests against fixture `.duckdb` stores comparing legacy output to Ibis output.
- Remove legacy raw SQL once golden tests pass; otherwise record an approved exception with exact reason.

### Wave 3: Functional pipeline conversion

- Convert analysis/history workflows to stage composition.
- Ensure pure stages only transform immutable domain data.
- Wrap Git/filesystem/database boundary failures into typed domain errors.
- Preserve CLI behavior and public contracts through adapter-level renderers.

### Wave 4: Tightening and removal

- Make guardrails stricter: no unapproved SQL string construction in ordinary read/query code.
- Remove unused imperative helpers and old query implementations.
- Confirm all direct DuckDB usages are boundary-approved and inventoried.
- Update maintainer docs with pipeline and Ibis examples.

## Testing Strategy

### Unit tests

- `Result` and pipeline composition combinators.
- Pure metric/transformation stages with immutable input fixtures.
- DomainError mapping and renderer behavior.
- Ibis expression builders at expression/schema level.

### Golden-output tests

- For every migrated query family, compare old vs new output over representative fixture stores.
- Compare columns, types, row counts, ordering where guaranteed, null behavior, numeric values, and JSON/RPC serialization.

### Integration tests

- `doctor`, `analyze`, `query`, `serve`/dashboard or `rpc` where currently supported.
- Existing `.ppi/history.duckdb` compatibility.
- Read-only query paths do not mutate store or require writer locks.

### Error-injection tests

- Invalid workspace.
- Git failure.
- parse/metric input failure.
- DuckDB lock failure.
- schema incompatibility.
- query execution failure.
- filesystem permission failure.

### Performance tests

- Small, medium, and large fixture repositories.
- Baseline before migration and compare after each wave.
- Watch for eager materialization, large immutable copies, and repeated Ibis execution.

## Architecture Guardrails

- No raw analytical SQL string construction outside `storage/duckdb_boundary.py` or test fixtures unless inventory-approved.
- No direct `duckdb` imports in `query`, `history`, `server`, or `cli` business logic modules.
- No Ibis expression execution inside pure expression-builder functions.
- No mutable cross-stage domain objects.
- No broad `except Exception` conversion into domain errors except at outermost boundary with logging/debug preservation.
- New query code must include either an Ibis expression builder test or an explicit exception inventory entry.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Ibis cannot express a DuckDB-specific query exactly | Query migration stalls | Keep exception inventory; isolate temporary boundary; add golden tests; revisit with Ibis alternative |
| Ibis changes ordering/null/type behavior | Public regression | Golden tests for ordering, nulls, numeric values, and serialization |
| Immutable models add overhead | Performance regression | Avoid large copies; keep columnar/relational data lazy; materialize only at boundaries |
| Result abstraction hides programmer errors | Debugging regression | Convert only known recoverable failures; allow invariant/programmer errors to raise |
| Big-bang refactor becomes too large | Delivery risk | Migrate by query family and pipeline slice; keep compatibility adapters stable |
| Direct SQL remains hidden in strings | Migration incomplete | Inventory scan + guardrail test + review checklist |

## Acceptance Gates

A wave is complete only when:

1. Inventory is updated and no unapproved raw analytical SQL remains for the touched area.
2. Public behavior tests pass for the touched CLI/RPC/dashboard surface.
3. Query migrations have golden-output coverage.
4. Result-based errors are rendered with stable codes/messages in machine-readable modes.
5. Performance smoke tests are within the accepted threshold or an explicit tradeoff is logged.

## Open Questions for Implementation

No blocking plan-level questions. The tasks phase should decide exact task IDs and sequence. Implementation may still discover specific Ibis limitations that require inventory exceptions.
