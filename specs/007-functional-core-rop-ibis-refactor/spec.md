# Feature Specification: Spec 007 — Functional Core, ROP, Typed Immutable Data & Ibis-First Refactor

**Feature ID**: `007-functional-core-rop-ibis-refactor`
**Feature Name**: `Spec 007 — Functional Core, ROP, Typed Immutable Data & Ibis-First Refactor`  
**Created**: 2026-07-03  
**Status**: Ready for Implementation Handoff  
**Updated**: 2026-07-04 — integrated checklist/analyze hardening for implementation handoff
**Input**: User description: "спланируй рефакторинг пайтон кода под функциональную парадигму программирования и Railway Oriented Programming: чистые функции, конвейерный код, неизменяемость данных, result based обработка исключений; и максимальный переезд пайтон кода взаимодействующего с duckdb на ibis-project/ibis".

## Clarifications

### Session 2026-07-03

- Q: Should the specification target an incremental, conservative migration or an ambitious maximum migration to functional pipelines and Ibis-based relational access? -> A: Target the maximum practical migration: Python business workflows should become explicit functional pipelines, raw analytical SQL should be eliminated from normal read/query paths, and Ibis functions/expressions should become the default interface for relational transformations, with direct DuckDB usage retained only as a documented infrastructure boundary or proven exception. The migration target is not stylistic: typed immutable domain models, pure functions, Result-returning recoverable flows, and Ibis expression builders are mandatory acceptance gates for migrated code.
- Q: Which `Result` and `Option` implementation should migrated code use? -> A: Use the existing `Expression` dependency as the canonical algebraic type provider: `expression.Result`, `Ok(...)` for success, and `Error(...)` for recoverable failure; `expression.Option`, `Some(...)`, and `Nothing` for optional domain values. Project-local helpers in `src/ppi/core/result.py` MAY re-export aliases or combinators, but MUST NOT introduce a second incompatible Result/Option representation.

## Overview

PPI is a Python Project Inspector that analyzes Git history metrics for Python/Odoo projects and stores analysis history in a DuckDB-backed local store. The current product surface includes CLI commands such as `doctor`, `analyze`, `serve`, `query`, and `rpc`, plus dashboard and VS Code integration paths that depend on reliable read/write access to persisted analysis results.

This feature refactors the Python analysis, history, storage, query, and server-facing data access paths so that business logic is expressed as predictable transformations, not as scattered side-effectful procedures. The desired end state is a codebase where core calculations are pure functions, every non-trivial workflow is assembled as an explicit pipeline, domain data is immutable by default, and recoverable failures are returned as typed results instead of being raised opportunistically through call stacks.

The refactor also makes expression-oriented relational access the default and expected path for reads and analytical transformations. Existing DuckDB persistence remains the storage engine unless a later decision changes it, but Python code that currently constructs or executes analytical DuckDB SQL is considered migration scope by default. Raw SQL and direct DuckDB calls are acceptable only at an intentionally named infrastructure boundary, or where an inventory entry proves that the operation cannot yet be represented safely, efficiently, or transactionally through Ibis.

The feature is a structural modernization with an ambitious default: migrate the codebase toward functional pipelines and Ibis-first query construction as far as practical while preserving existing observable CLI, dashboard, RPC, storage, and test behavior. Incremental delivery is allowed, but the end-state specification must not normalize parallel long-term implementations, scattered raw SQL, or side-effectful domain logic.


## Ambition Standard: Not a Cosmetic Refactor

This specification intentionally treats the work as an architectural migration, not a cleanup pass. A change is not accepted merely because code is split into helper functions, wrappers are introduced, or raw SQL is moved to a different module. The accepted outcome is a measurable shift in the shape of the codebase: workflows become stage-composed pipelines, recoverable failure flow is value-based, stage-boundary data is immutable and typed, and relational read/query logic is expressed as Ibis expressions by default.

The migration scope includes the Python paths that support the documented PPI surfaces: `doctor`, `analyze`, `query`, `serve`, `rpc`, dashboard data access, VS Code bridge/RPC reads, history ingestion, history read models, and storage-facing query helpers. Any implementation plan that migrates only leaf utilities or a single demonstration path fails this specification unless the remaining areas are explicitly inventoried with owners, removal conditions, and dates/versions for follow-up.

## Non-Negotiable Architectural Gates

The refactor is considered incomplete unless migrated production code satisfies all of the following gates:

1. **Pure functional core**: domain computation, normalization, validation, read-model shaping, and query-expression construction MUST be pure functions with explicit inputs and deterministic outputs. They MUST NOT read runtime globals, environment variables, clocks, live connections, or mutable singleton state.
2. **Typed immutable data**: data crossing pipeline stage boundaries MUST be represented by explicitly typed immutable structures. Acceptable shapes include frozen dataclasses, `typing.NamedTuple`, `TypedDict` for serialized/public shapes where mutation is not exposed, or Pydantic/frozen model equivalents if already adopted. Plain mutable dictionaries/lists MAY appear only inside parsing or serialization boundaries and MUST be converted before entering the functional core.
3. **Result-based recoverable errors**: expected failures MUST be represented as `Result[T, DomainError]`. Migrated domain and pipeline stages MUST NOT signal expected failure through `raise`, `None`, sentinel values, partial dictionaries, boolean flags, or swallowed exceptions.
4. **Exception boundary rule**: exceptions are allowed for programmer errors, invariant violations, truly unexpected defects, and wrapping external library calls at an adapter boundary. Boundary code MUST convert expected external failures into typed `Error(DomainError)` before returning to the pipeline.
5. **Pipeline as architecture**: non-trivial workflows MUST be composed from named stages with clear pure/boundary classification. A long imperative function that calls helper functions is not sufficient.
6. **Ibis-first relational logic**: read/query/analytics code MUST build Ibis expressions/functions instead of raw SQL. Raw SQL must not be moved to a helper as a workaround; it must either be eliminated, isolated in an approved DuckDB boundary, or tracked as an explicit exception.
7. **Mandatory type checking gate**: the refactor MUST include static typing coverage for the new core Result, error, pipeline, immutable model, Ibis builder, and stage modules. A migrated module is not accepted if its public stage/builder interfaces are untyped or rely on `Any` for domain values without a documented reason.
8. **Option for domain absence**: optional domain values in migrated core/pipeline/query code MUST use `expression.Option` (`Some(...)` / `Nothing`) instead of `None`, sentinel objects, missing dict keys, or empty strings. `None` remains acceptable only at external library, serializer, CLI/JSON/RPC, or Pydantic boundary adapters where the public contract already uses null.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run existing analysis flows after refactor (Priority: P1)

As a developer maintaining PPI, I want the existing analysis and query workflows to behave the same after refactoring, so that users receive the same metrics while the internals become more maintainable.

**Why this priority**: The refactor is only valuable if it preserves product behavior. CLI and dashboard regressions would block all later improvements.

**Independent Test**: Run the existing test suite and smoke-test the documented CLI commands against a representative Git repository before and after the refactor; compare the produced analysis status and query outputs.

**Acceptance Scenarios**:

1. **Given** a repository that currently analyzes successfully, **When** the refactored `analyze` workflow is run, **Then** it completes with the same run status semantics and produces queryable history results.
2. **Given** an existing history store, **When** the refactored `query` or `rpc` read path is used, **Then** it returns response shapes compatible with the dashboard and VS Code bridge contracts.
3. **Given** a known invalid workspace or broken repository, **When** analysis is attempted, **Then** the user-facing error remains readable and actionable.

---

### User Story 2 - Compose analysis as functional pipelines (Priority: P1)

As a Python developer working on PPI internals, I want analysis steps to be represented as explicit, testable pipelines, so that each transformation can be validated independently and failures can be composed without hidden control flow.

**Why this priority**: This is the core maintainability goal. It reduces coupling between Git scanning, parsing, metric calculation, persistence, and reporting.

**Independent Test**: Unit-test representative pipeline stages with immutable inputs and verify that each stage returns a success or failure result without mutating shared state. Architecture tests or static checks verify that core workflow modules depend on pipeline/result abstractions instead of ad-hoc imperative orchestration.

**Acceptance Scenarios**:

1. **Given** a pipeline stage receives valid input data, **When** it runs, **Then** it returns a successful result containing the transformed value and no hidden mutation of the input.
2. **Given** a pipeline stage encounters a recoverable domain or IO error, **When** it runs, **Then** it returns a failure result with typed error information instead of relying on uncaught exceptions for ordinary control flow.
3. **Given** multiple stages are composed, **When** one stage fails, **Then** later dependent stages are skipped and the final result explains the failing stage.

---

### User Story 3 - Centralize relational access through a query abstraction (Priority: P1)

As a maintainer of storage and query code, I want relational reads and analytical transformations to use a single expression-oriented access layer where possible, so that DuckDB-specific code is isolated and easier to replace, optimize, and test.

**Why this priority**: PPI's history store and dashboard queries are core product capabilities. Consolidating data access prevents SQL drift and makes the codebase more portable.

**Independent Test**: For each query family, classify it as Ibis-migrated or justified DuckDB-boundary code; run golden-output tests comparing old and new outputs over the same fixture store before removing the legacy implementation.

**Acceptance Scenarios**:

1. **Given** a read query that can be represented through the target query abstraction, **When** it is migrated, **Then** callers receive the same columns, types, null behavior, ordering guarantees, and error semantics as before.
2. **Given** a storage operation that cannot yet be represented safely through the abstraction, **When** it remains DuckDB-specific, **Then** that exception is documented in a migration inventory with a reason and owner.
3. **Given** a dashboard or RPC endpoint depends on a migrated query, **When** the endpoint is called, **Then** its public response contract remains backward compatible.
4. **Given** new relational read/query code is added, **When** it is reviewed, **Then** it uses Ibis expressions/functions by default and does not introduce raw analytical SQL unless an approved boundary exception is recorded.
5. **Given** an existing raw SQL query is discovered in a read/query path, **When** it is assessed, **Then** the default decision is migration to Ibis unless the inventory records a concrete unsupported feature, performance regression, or transactional constraint.

---

### User Story 4 - Make error handling explicit and user-facing behavior stable (Priority: P2)

As a CLI and dashboard user, I want failures to be reported consistently, so that errors are diagnosable without exposing internal stack traces unless debug output is requested.

**Why this priority**: Railway-oriented error handling should improve reliability, but it must also preserve useful diagnostics.

**Independent Test**: Inject representative failures in Git access, parsing, lock acquisition, schema compatibility, query execution, and filesystem access; verify typed result propagation and user-facing messages.

**Acceptance Scenarios**:

1. **Given** a recoverable failure occurs during analysis, **When** the pipeline terminates, **Then** the top-level command receives a structured failure and renders a clear message.
2. **Given** an unexpected programmer error occurs, **When** it propagates, **Then** it is not silently converted into a misleading domain result.
3. **Given** JSON or RPC output mode is active, **When** a failure occurs, **Then** the machine-readable response includes a stable error code and message field.

---

### User Story 5 - Preserve performance and storage compatibility (Priority: P2)

As a user analyzing real repositories, I want refactored code to stay performant and compatible with existing local history stores, so that the modernization does not make analysis or dashboard usage noticeably worse.

**Why this priority**: Data abstraction and immutable data can introduce overhead if applied carelessly.

**Independent Test**: Run performance smoke tests against representative small, medium, and large repositories; compare key operations against current baselines.

**Acceptance Scenarios**:

1. **Given** an existing `.ppi/history.duckdb` store, **When** the refactored code reads it, **Then** it does not require a destructive rebuild unless the schema is already incompatible for independent reasons.
2. **Given** a representative repository, **When** analysis and dashboard queries run after refactoring, **Then** runtime and memory usage remain within agreed thresholds.
3. **Given** a query uses the abstraction layer, **When** it is evaluated, **Then** unnecessary eager materialization is avoided unless a boundary explicitly requires concrete results.

## Edge Cases

- A pipeline stage needs both deterministic transformation and access to time, filesystem, subprocesses, Git, or the database.
- Existing mutable structures are shared by callers that expect in-place updates.
- A recoverable domain failure is accidentally swallowed and converted to a successful empty result.
- An unexpected programming error is incorrectly hidden inside a generic failure result.
- A query has backend-specific SQL features that the expression abstraction cannot represent.
- Query migration changes row ordering, null handling, numeric precision, timestamp behavior, or column naming.
- Long-running analysis holds writer locks while read-only dashboard or RPC sessions are active.
- Refactored code breaks JSON output, RPC response shape, or dashboard assumptions even if internal tests pass.
- Existing stores created by older versions are missing tables or contain partial/cancelled runs.
- Immutable data modeling creates excessive object copying on large histories.
- A query mixes business filtering/aggregation with storage-maintenance SQL, making the Ibis migration boundary unclear.
- A convenience helper reintroduces raw SQL string construction outside the approved database boundary.
- A pipeline stage becomes nominally functional but still reads global state, current time, environment variables, or a live database connection implicitly.

- An implementation claims Ibis migration while still materializing large tables early and performing relational joins/aggregations in Python loops.
- A public query family is migrated, but its legacy SQL path remains callable indefinitely without a removal condition.
- A workflow is decomposed into stages but stage inputs/outputs are untyped or mutable, making the pipeline only nominally functional.
- A guardrail relies only on documentation and review rather than failing tests/scripts that can block regressions.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The refactor MUST preserve existing user-facing CLI commands, documented global options, and dashboard/RPC response contracts unless a change is explicitly documented as out of scope for this feature.
- **FR-002**: Core domain transformations MUST be organized as pure functions where their outputs depend only on explicit inputs; hidden reads from global state, clocks, environment variables, live database connections, or mutable singletons are not acceptable inside domain transformations.
- **FR-003**: Side effects such as filesystem access, Git process interaction, database IO, logging, clocks, environment variables, and CLI rendering MUST be isolated at workflow boundaries or dedicated adapter layers and passed into pipelines through explicit inputs or ports.
- **FR-004**: Analysis, history ingestion, storage read-model construction, query serving, dashboard/RPC data preparation, and non-trivial CLI/server orchestration workflows MUST be implemented as explicit named pipelines where each stage receives typed immutable input and returns `Result[TypedValue, DomainError]` unless the stage is a pure total function that cannot fail.
- **FR-005**: Recoverable errors MUST use `expression.Result[T, DomainError]` propagation with `Ok(...)` for success and `Error(DomainError)` for failure, plus stable error categories, stable codes, stage context, and human-readable messages; expected failures MUST NOT be represented by exceptions, `None`, sentinel values, booleans, ad-hoc error dictionaries, or a second custom Result implementation inside migrated flows.
- **FR-005A**: Optional domain values in migrated core, pipeline, query, Ibis-builder, and DTO-mapping internals MUST use `expression.Option[T]` with `Some(...)` or `Nothing`; `None` may cross only external/public boundaries and MUST be converted to/from `Option` before entering or after leaving domain stages.
- **FR-006**: Unexpected programmer errors MUST remain distinguishable from recoverable domain failures and MUST NOT be silently hidden as ordinary empty results.
- **FR-007**: Domain data passed between pipeline stages MUST be immutable and explicitly typed by default; mutable accumulators MAY exist only inside tightly scoped performance-sensitive internals, MUST be hidden inside a pure facade, MUST not cross stage boundaries, and MUST have tests proving callers cannot observe mutation.
- **FR-008**: Public JSON, RPC, and dashboard-facing outputs MUST preserve their existing field names, data shapes, ordering guarantees, and null semantics unless a compatibility note and migration path are provided.
- **FR-009**: The project MUST maintain a migration inventory of all Python modules/functions that directly interact with DuckDB, construct raw SQL strings, execute SQL text, mutate/read DuckDB-backed data, manage schema/transactions/locks, perform bulk import/export, or expose database-shaped data to callers.
- **FR-010**: Every DuckDB-interacting read/query/analytical transformation path MUST be migrated to Ibis expressions/functions by default; a path may remain non-Ibis only when the migration inventory records a specific unsupported capability, unacceptable verified performance regression, transaction/schema concern, or other approved boundary reason.
- **FR-011**: Direct DuckDB usage MAY remain only for connection lifecycle, storage-file management, locking, schema initialization, migrations, transactions, pragmas, backend-specific maintenance, bulk import/export mechanics, or proven unsupported query/write features; each remaining direct usage MUST be isolated behind an explicit boundary module and justified in the migration inventory.
- **FR-011A**: New or modified relational read/query code MUST NOT introduce raw analytical SQL string construction outside the approved DuckDB boundary; it MUST use Ibis table/expression/function composition unless an exception is recorded before merge.
- **FR-011B**: Ibis builders MUST be pure, typed functions that construct lazy expressions only; they MUST NOT execute expressions, open DuckDB connections, read configuration, construct SQL strings, or materialize results.
- **FR-012**: Migrated query paths MUST be covered by golden-output tests comparing old and new behavior over representative fixture data before the legacy implementation is removed.
- **FR-013**: Storage schema compatibility MUST be preserved for existing history stores unless a separate migration is explicitly introduced.
- **FR-014**: Read-only query paths MUST remain read-only and MUST NOT acquire writer locks or mutate history data.
- **FR-015**: Write paths MUST retain single-writer safety and existing lock/recovery semantics.
- **FR-016**: Refactored pipelines MUST expose enough stage-level context for diagnostics, including stage name, error category, and causal message.
- **FR-017**: The refactor MUST include regression coverage for CLI text mode, JSON output mode, query output mode, RPC mode, and server/dashboard data access where those modes are currently supported.
- **FR-018**: Performance-sensitive paths MUST avoid unnecessary eager materialization of relational data and large immutable copies while preserving immutable stage boundaries through structural sharing, lazy Ibis expressions, tuples/frozen containers, or boundary-local mutation hidden behind pure interfaces.
- **FR-019**: The refactor MUST provide an adoption path that allows incremental migration by module or query family without requiring a single large-bang rewrite, while still tracking toward the end state of no ordinary read/query business logic written as raw SQL.
- **FR-020**: Documentation for maintainers MUST describe the new pipeline, Result, typed immutability, pure-function, exception-boundary, and Ibis-first data-access conventions with examples, including explicit examples of acceptable and unacceptable raw SQL, mutation, untyped DTOs, and exception-driven domain flow.
- **FR-021**: New core primitives, immutable models, pipeline stages, Ibis builders, public DTO mappers, and error renderers MUST have explicit type annotations and static type checks. Use of `Any` in these modules MUST be justified by an interop boundary and tracked in review notes.
- **FR-022**: Migrated workflows MUST include architecture guardrails that detect mutable stage-boundary DTOs, untyped public stage signatures, broad recoverable exception raising/catching in domain code, and unapproved raw SQL/DuckDB calls.

- **FR-023**: The migration inventory MUST be module-aware, not only grep-based: each entry MUST identify the public surface or internal workflow it supports, current owner/module, current pattern, target pattern, disposition, removal condition, and validation evidence.
- **FR-024**: Temporary dual legacy/Ibis paths MAY exist only during parity work; each dual path MUST have a removal condition tied to golden-output parity and MUST NOT become an accepted steady state.
- **FR-025**: At least one end-to-end vertical slice for each P1 surface family (`analyze`/history ingestion, CLI `query`, RPC/dashboard read access, and storage read models) MUST be planned for migration, not merely a single proof-of-concept helper.
- **FR-026**: Architecture guardrails MUST be executable and review-blocking: they MUST fail on unapproved raw analytical SQL, unapproved direct DuckDB imports/calls, untyped migrated stage/builder interfaces, mutable stage-boundary DTOs, and exception-driven recoverable domain flow.
- **FR-027**: Ibis adoption MUST not be used as an excuse for eager materialization; relational filtering, joining, aggregation, projection, ordering, and limiting SHOULD remain lazy Ibis expressions until the execution boundary materializes the exact public result shape.
- **FR-028**: Public compatibility evidence MUST be tied to named query families and public surfaces, not only to aggregate test-suite success.
- **FR-029**: The implementation MUST define an explicit package/module dependency direction for core, pipeline, query expression builders, DuckDB/Ibis execution boundaries, CLI, server, and VS Code/RPC adapters; migrated core/query modules MUST NOT import adapter layers.
- **FR-030**: Completion evidence MUST include a final architecture review that lists pass/fail status for pure functional core, typed immutability, Result-only recoverable failures, Ibis-first relational access, raw SQL exceptions, direct DuckDB boundary exceptions, and public behavior compatibility.
- **FR-031**: All write, ingestion, bulk-load, schema, migration, lock, transaction, and maintenance paths that interact with DuckDB MUST be explicitly dispositioned. Where Ibis can safely express the operation while preserving storage compatibility and transaction semantics, the path SHOULD migrate to the Ibis/backend abstraction; where direct DuckDB remains necessary, it MUST be isolated as a named boundary exception with owner, rationale, tests, and a future re-evaluation condition.

### Key Entities

- **Pipeline Stage**: A named transformation or boundary operation that consumes explicit input and returns a typed result.
- **Result**: A success or failure value used to compose workflows without ordinary recoverable exceptions controlling the flow.
- **Domain Error**: A typed, recoverable failure with stable category, readable message, and optional cause/context.
- **Immutable Domain Model**: A data object passed across stages without shared mutation.
- **Ibis Query Expression**: A backend-evaluable relational expression composed through Ibis APIs and used for reads and analytical transformations.
- **DuckDB Boundary**: A remaining direct DuckDB interaction that is intentionally isolated, infrastructure-focused, and documented as an exception to Ibis-first access.
- **Migration Inventory**: A living list of direct database interactions, migration status, rationale, and test coverage.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of existing automated tests pass after the refactor, with additional regression coverage for migrated query families.
- **SC-002**: 100% of discovered read/query code paths that directly construct analytical DuckDB SQL are either migrated to Ibis or listed as approved DuckDB-boundary exceptions; the target outcome is zero unapproved raw analytical SQL in normal read/query business logic.
- **SC-003**: 100% of remaining direct DuckDB usages and raw SQL string construction sites are listed in the migration inventory with a reason, owner, test coverage, and future decision status.
- **SC-004**: Representative CLI workflows (`doctor`, `analyze`, `query`, `serve`/dashboard or `rpc` where applicable) produce compatible user-facing behavior against fixture repositories.
- **SC-005**: Golden-output tests show no unintended differences in migrated query results for columns, row counts, ordering where guaranteed, null handling, and numeric values.
- **SC-006**: Recoverable failures in representative pipeline stages are returned as typed result failures and rendered with stable error codes/messages in machine-readable modes.
- **SC-007**: Analysis and dashboard/query smoke-test runtime remains within 15% of the pre-refactor baseline for representative fixture repositories, unless a specific tradeoff is accepted in the decision log.
- **SC-008**: New or updated maintainer documentation explains how to add a pipeline stage, how to model errors, how to add an Ibis relational query, and how to request/justify a rare DuckDB-boundary exception without bypassing the data-access abstraction.

- **SC-009**: The query-family inventory has 100% disposition coverage for documented CLI query metrics, RPC methods, dashboard/server datasets, history read models, and VS Code bridge read surfaces: `ibis_migrated`, `approved_boundary_exception`, `removed`, or `not_applicable_false_positive`; no item remains `unknown`.
- **SC-010**: No migrated P1 workflow is accepted while its public stage interfaces are untyped, its stage-boundary domain data is mutable, or its recoverable domain failures use exceptions/`None`/sentinel values.
- **SC-011**: Every temporary dual legacy/Ibis path has a documented removal condition and final status; final completion has zero permanent dual implementations for normal read/query business logic.
- **SC-012**: Final architecture review records executable evidence for every non-negotiable architectural gate, including the command/test that produced the evidence and any accepted exception IDs.
- **SC-013**: The final migration inventory has 100% disposition coverage for all direct DuckDB interactions, including reads, analytical queries, writes, ingestion, bulk operations, schema/migration, transactions, locks, maintenance, tests, and false positives; every non-Ibis production entry has an approved boundary category and re-evaluation condition.

## Assumptions

- DuckDB remains the persistence engine for the existing history store in this feature; the refactor targets Python-side interaction patterns, not a storage-engine replacement.
- The target query abstraction is Ibis, as requested, with DuckDB as the primary backend for local execution.
- Existing stores under `.ppi/history.duckdb` must remain readable unless they are already incompatible with the current application schema.
- The refactor can be delivered incrementally by module or query family, with compatibility tests guarding each migration.
- Raw SQL and direct DuckDB APIs are treated as exceptions, not a parallel style: they are acceptable only where required for correctness, verified performance, transactions, schema/maintenance operations, bulk mechanics, or unsupported Ibis features, and must be isolated plus inventoried.

## Out of Scope

- Replacing DuckDB as the underlying storage file format.
- Redesigning the dashboard UI or VS Code extension user experience.
- Introducing distributed execution, new storage backends, or a new worker runtime.
- Changing metric definitions unless a pre-existing bug is documented and explicitly accepted.
- Rewriting TypeScript/frontend code except where required to preserve response contracts during backend refactoring.
