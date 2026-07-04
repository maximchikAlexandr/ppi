# Tasks: Spec 007 — Functional Core, ROP, Typed Immutable Data & Ibis-First Refactor

**Input**: Design artifacts from `specs/007-functional-core-rop-ibis-refactor/`  
**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`, `architecture-review.md`  
**Goal**: Convert PPI's Python internals to strict functional pipelines, Railway Oriented Programming, typed immutable domain data, Result-only recoverable errors, and Ibis-first relational access while preserving public behavior.

## Task Format Rules

All implementation tasks use this format:

```text
- [X] T001 Description with file path
- [X] T002 [P] Description with file path
- [X] T010 [P] [US1] Description with file path
- [X] T011 [US1] Description with file path
```

`[P]` means the task can run in parallel after its phase prerequisites are complete and touches independent files. `[USn]` maps to a user story from `spec.md`.

## User Story Mapping

| Story | Priority | Focus | Independent validation |
|---|---:|---|---|
| US1 | P1 | Existing analysis/query behavior remains compatible | Existing tests + CLI/RPC/dashboard smoke + golden outputs |
| US2 | P1 | Analysis and history workflows become functional pipelines | Stage tests + Result short-circuit tests + architecture guards |
| US3 | P1 | Relational read/query access becomes Ibis-first | Query-family inventory + legacy-vs-Ibis golden tests + raw SQL guardrails |
| US4 | P2 | Error handling becomes explicit and stable | Error injection tests for CLI/RPC/server/query/storage |
| US5 | P2 | Maintainers can safely extend the new architecture | Docs, examples, review checklist, no-regression guardrails |

## Phase 1: Setup

**Purpose**: Establish refactor scaffolding, dependency visibility, and validation entry points before changing behavior.

- [X] T001 Add Ibis dependency and DuckDB backend extras to project dependency metadata in `pyproject.toml`
- [X] T002 [P] Add refactor validation command group or script entry with `--inventory`, `--guardrails`, `--golden`, `--performance`, `--typing`, `--immutability`, `--result-flow`, and `--ibis` modes in `scripts/validate_functional_ibis_refactor.py`
- [X] T003 [P] Define migration inventory schema and required evidence fields in `specs/007-functional-core-rop-ibis-refactor/data-model.md`
- [X] T004 [P] Keep contributor-facing refactor guidance in `specs/007-functional-core-rop-ibis-refactor/quickstart.md`
- [X] T005 Add test fixture layout for representative `.ppi/history.duckdb` stores in `tests/fixtures/history_stores/README.md`
- [X] T006 Add baseline smoke-test harness for documented CLI surfaces in `tests/smoke/test_cli_surfaces_baseline.py`

## Phase 2: Foundational Prerequisites

**Purpose**: Build shared primitives and hard guardrails that block all user-story work.

- [X] T007 Implement `src/ppi/core/result.py` as the canonical PPI wrapper around `Expression`: re-export `Result`, `Ok`, `Error`, `Option`, `Some`, and `Nothing`, and add typed `map`, `bind`, `tap`, `recover`, and `collect` helpers without creating a second Result/Option representation
- [X] T008 Implement stable `DomainError`, `ErrorCode`, error categories, causal context, and debug-safe detail fields in `src/ppi/core/errors.py`
- [X] T009 Implement `Stage`, `Pipeline`, stage metadata, short-circuit composition, and boundary/pure markers in `src/ppi/core/pipeline.py`
- [X] T010 [P] Implement immutable collection and frozen-model helper utilities in `src/ppi/core/immutable.py`
- [X] T011 [P] Add unit tests proving `src/ppi/core/result.py` composes `Expression` `Ok`/`Error` and `Some`/`Nothing` values without introducing incompatible Result or Option types in `tests/unit/core/test_result.py`
- [X] T012 [P] Add unit tests for pipeline short-circuiting and stage metadata in `tests/unit/core/test_pipeline.py`
- [X] T013 [P] Add unit tests for `DomainError` serialization and safe debug details in `tests/unit/core/test_errors.py`
- [X] T014 Create architecture guardrail test that fails on direct DuckDB imports outside approved modules in `tests/architecture/test_duckdb_boundaries.py`
- [X] T015 Create architecture guardrail test that fails on raw analytical SQL strings outside approved modules/tests in `tests/architecture/test_raw_sql_guardrails.py`
- [X] T016 Create architecture guardrail test that checks migrated core/query modules do not import CLI/server adapters in `tests/architecture/test_layering.py`
- [X] T017 Add CI/test documentation for running guardrails locally in `specs/007-functional-core-rop-ibis-refactor/quickstart.md`
- [X] T018 Implement migration inventory loader, validator, and status reporter in `src/ppi/storage/inventory.py`
- [X] T019 Add tests for migration inventory validation and exception requirements in `tests/unit/storage/test_migration_inventory.py`
- [X] T020 Record direct DuckDB/raw SQL inventory requirements and status fields in `specs/007-functional-core-rop-ibis-refactor/contracts/data-access-contract.md`
- [X] T021 Define query-family inventory template covering CLI, RPC, dashboard, server, and history consumers in `specs/007-functional-core-rop-ibis-refactor/contracts/data-access-contract.md`
- [X] T022 Record first query-family disposition expectations in `specs/007-functional-core-rop-ibis-refactor/architecture-review.md`
- [X] T023 Add anti-laziness review checklist for pipeline/Ibis migrations in `specs/007-functional-core-rop-ibis-refactor/checklists/ambition-quality.md`

## Phase 3: User Story 3 - Centralize Relational Access Through Ibis (P1)

**Independent Test**: For each query family, legacy and Ibis implementations produce identical public output over fixture stores before the legacy path is removed.

- [X] T024 [P] [US3] Implement approved DuckDB infrastructure boundary for connection lifecycle, schema, lock, transaction, maintenance, and write mechanics in `src/ppi/storage/duckdb_boundary.py`
- [X] T025 [P] [US3] Add tests proving only approved boundary categories use direct DuckDB in `tests/unit/storage/test_duckdb_boundary.py`
- [X] T026 [US3] Implement Ibis DuckDB backend binding and table registry in `src/ppi/storage/ibis_backend.py`
- [X] T027 [P] [US3] Add tests for Ibis backend binding over fixture history stores in `tests/integration/storage/test_ibis_backend.py`
- [X] T028 [P] [US3] Define immutable query parameter models for history/query/dashboard/RPC reads in `src/ppi/query/contracts.py`
- [X] T029 [US3] Implement first-wave Ibis expression builders for history run/status/read-model queries in `src/ppi/storage/ibis_queries.py`
- [X] T030 [US3] Implement Ibis expression builders for CLI `query` output families in `src/ppi/query/ibis_queries.py`
- [X] T031 [US3] Implement Ibis expression builders for dashboard/server data families in `src/ppi/server/ibis_queries.py`
- [X] T032 [US3] Implement Ibis expression builders for RPC/VS Code bridge query families in `src/ppi/query/rpc_ibis_queries.py`
- [X] T033 [P] [US3] Implement pure mappers from tabular query results to public DTOs in `src/ppi/query/read_models.py`
- [X] T034 [P] [US3] Implement golden comparison utilities for legacy SQL vs Ibis outputs in `tests/golden/query_golden_utils.py`
- [X] T035 [US3] Add golden tests for history read-model query families in `tests/golden/test_history_read_models_ibis.py`
- [X] T036 [US3] Add golden tests for CLI `query` families in `tests/golden/test_cli_query_ibis.py`
- [X] T037 [US3] Add golden tests for dashboard/server query families in `tests/golden/test_dashboard_queries_ibis.py`
- [X] T038 [US3] Add golden tests for RPC/VS Code bridge query families in `tests/golden/test_rpc_queries_ibis.py`
- [X] T039 [US3] Route normal history read-model paths through Ibis builders and execution boundary in `src/ppi/history/read_models.py`
- [X] T040 [US3] Route normal CLI query paths through Ibis builders and DTO mappers in `src/ppi/cli/commands/query.py`
- [X] T041 [US3] Route normal dashboard/server query paths through Ibis builders and DTO mappers in `src/ppi/server/handlers/query.py`
- [X] T042 [US3] Route normal RPC/VS Code bridge query paths through Ibis builders and DTO mappers in `src/ppi/query/rpc.py`
- [X] T043 [US3] Remove or disable legacy raw SQL path for history read-models after golden parity in `src/ppi/history/read_models.py`
- [X] T044 [US3] Remove or disable legacy raw SQL path for CLI query after golden parity in `src/ppi/cli/commands/query.py`
- [X] T045 [US3] Remove or disable legacy raw SQL path for dashboard/server queries after golden parity in `src/ppi/server/handlers/query.py`
- [X] T046 [US3] Remove or disable legacy raw SQL path for RPC queries after golden parity in `src/ppi/query/rpc.py`
- [X] T047 [US3] Update `specs/007-functional-core-rop-ibis-refactor/architecture-review.md` with migrated, removed, and approved-exception query-family statuses
- [X] T048 [US3] Tighten raw SQL guardrail to fail on any new read/query/analytics SQL outside approved boundaries in `tests/architecture/test_raw_sql_guardrails.py`

## Phase 4: User Story 2 - Compose Analysis as Functional Pipelines (P1)

**Independent Test**: Representative analysis and history ingestion workflows are stage-composed; pure stages have deterministic tests and recoverable failures short-circuit through `Result`.

- [X] T049 [P] [US2] Define frozen history domain models for commits, files, metrics, analysis runs, and write batches in `src/ppi/history/models.py`
- [X] T050 [P] [US2] Define immutable runtime context and boundary handles for analysis pipelines in `src/ppi/runtime/context.py`
- [X] T051 [US2] Implement pure validation stages for repository/workspace/analyze options in `src/ppi/history/stages_validation.py`
- [X] T052 [US2] Implement Git/filesystem boundary stages that convert expected external failures into `DomainError` in `src/ppi/history/stages_boundary.py`
- [X] T053 [US2] Implement pure normalization stages for commits/files/project snapshots in `src/ppi/history/stages_normalize.py`
- [X] T054 [US2] Implement pure metric computation stages over immutable inputs in `src/ppi/history/stages_metrics.py`
- [X] T055 [US2] Implement write-preparation stages that produce immutable write batches without performing DB IO in `src/ppi/history/stages_write_prep.py`
- [X] T056 [US2] Implement history write boundary stage using approved DuckDB boundary in `src/ppi/history/stages_write_boundary.py`
- [X] T057 [US2] Compose analyze/history ingestion pipeline in `src/ppi/history/pipeline.py`
- [X] T058 [US2] Replace imperative analyze orchestration with pipeline invocation in `src/ppi/cli/commands/analyze.py`
- [X] T059 [US2] Add unit tests for pure validation stages in `tests/unit/history/test_stages_validation.py`
- [X] T060 [US2] Add unit tests for pure normalization stages in `tests/unit/history/test_stages_normalize.py`
- [X] T061 [US2] Add unit tests for pure metric stages in `tests/unit/history/test_stages_metrics.py`
- [X] T062 [US2] Add unit tests for write-preparation stages in `tests/unit/history/test_stages_write_prep.py`
- [X] T063 [US2] Add boundary failure tests for Git/filesystem/write stages in `tests/unit/history/test_boundary_stage_errors.py`
- [X] T064 [US2] Add integration test proving analyze pipeline short-circuits on stage failure in `tests/integration/history/test_analyze_pipeline_errors.py`
- [X] T065 [US2] Add architecture guardrail that migrated history stages do not mutate cross-stage DTOs in `tests/architecture/test_immutable_stage_boundaries.py`

## Phase 5: User Story 1 - Preserve Existing Public Behavior (P1)

**Independent Test**: Existing documented CLI, query, RPC, and dashboard/server behavior remains compatible over representative repositories and history stores.

- [X] T066 [US1] Capture pre-refactor public output fixtures for `doctor`, `analyze`, `query`, `serve`, and `rpc` in `tests/golden/public_behavior/README.md`
- [X] T067 [US1] Add CLI compatibility tests for `doctor` output and exit semantics in `tests/golden/public_behavior/test_doctor_compatibility.py`
- [X] T068 [US1] Add CLI compatibility tests for `analyze` success/failure semantics in `tests/golden/public_behavior/test_analyze_compatibility.py`
- [X] T069 [US1] Add CLI compatibility tests for `query` output contracts in `tests/golden/public_behavior/test_query_compatibility.py`
- [X] T070 [US1] Add server/dashboard compatibility tests for response shapes in `tests/golden/public_behavior/test_dashboard_compatibility.py`
- [X] T071 [US1] Add RPC/VS Code bridge compatibility tests for JSON response shapes in `tests/golden/public_behavior/test_rpc_compatibility.py`
- [X] T072 [US1] Ensure CLI adapters only parse input, call pipelines, and render results in `src/ppi/cli/commands/__init__.py`
- [X] T073 [US1] Ensure server handlers only parse requests, call query pipelines, and render DTOs in `src/ppi/server/handlers/__init__.py`
- [X] T074 [US1] Add smoke test that runs a full analyze -> query -> server/RPC read sequence in `tests/smoke/test_end_to_end_functional_ibis.py`
- [X] T075 [US1] Add fixture upgrade/backward-compatibility test for existing `.ppi/history.duckdb` stores in `tests/integration/storage/test_existing_history_store_compatibility.py`

## Phase 6: User Story 4 - Make Error Handling Explicit and Stable (P2)

**Independent Test**: Expected failures in Git, filesystem, schema, lock, Ibis execution, query validation, and server/RPC rendering return typed errors with stable user-facing shapes.

- [X] T076 [P] [US4] Implement text and JSON error renderers for CLI adapters in `src/ppi/cli/render_errors.py`
- [X] T077 [P] [US4] Implement RPC/server error DTO mapping from `DomainError` in `src/ppi/server/error_responses.py`
- [X] T078 [US4] Replace ad-hoc expected exception handling in CLI commands with `Result` rendering in `src/ppi/cli/commands/analyze.py`
- [X] T079 [US4] Replace ad-hoc expected exception handling in query CLI with `Result` rendering in `src/ppi/cli/commands/query.py`
- [X] T080 [US4] Replace ad-hoc expected exception handling in server/RPC handlers with `Result` rendering in `src/ppi/server/handlers/query.py`
- [X] T081 [US4] Map Ibis/DuckDB execution failures to stable `DomainError` values in `src/ppi/storage/ibis_backend.py`
- [X] T082 [US4] Map lock/schema/history-store failures to stable `DomainError` values in `src/ppi/storage/duckdb_boundary.py`
- [X] T083 [US4] Add error-injection tests for Git and filesystem failures in `tests/integration/errors/test_git_filesystem_errors.py`
- [X] T084 [US4] Add error-injection tests for schema, lock, and storage failures in `tests/integration/errors/test_storage_errors.py`
- [X] T085 [US4] Add error-injection tests for Ibis query execution failures in `tests/integration/errors/test_ibis_query_errors.py`
- [X] T086 [US4] Add CLI text/JSON error rendering contract tests in `tests/unit/cli/test_render_errors.py`
- [X] T087 [US4] Add RPC/server error response contract tests in `tests/unit/server/test_error_responses.py`

## Phase 7: User Story 5 - Maintainer Extension and Anti-Regression Guardrails (P2)

**Independent Test**: A contributor can add a new query family or pipeline stage by following docs and tests; guardrails reject lazy raw SQL or imperative workflow regressions.

- [X] T088 [P] [US5] Document how to add a new Ibis query family in `specs/007-functional-core-rop-ibis-refactor/contracts/data-access-contract.md`
- [X] T089 [P] [US5] Document how to add a new pipeline stage and stage tests in `specs/007-functional-core-rop-ibis-refactor/contracts/pipeline-contract.md`
- [X] T090 [P] [US5] Document approved DuckDB boundary exceptions and required inventory evidence in `specs/007-functional-core-rop-ibis-refactor/contracts/data-access-contract.md`
- [X] T091 [US5] Add example minimal Ibis query-family test fixture in `tests/examples/test_new_ibis_query_family_example.py`
- [X] T092 [US5] Add example pipeline stage test fixture in `tests/examples/test_new_pipeline_stage_example.py`
- [X] T093 [US5] Add review checklist enforcement notes to `specs/007-functional-core-rop-ibis-refactor/checklists/ambition-quality.md`
- [X] T094 [US5] Add CI-oriented command that runs inventory validation, architecture tests, golden tests, smoke tests, and performance modes through `scripts/validate_functional_ibis_refactor.py`
- [X] T095 [US5] Update developer quickstart for the refactor validation workflow in `specs/007-functional-core-rop-ibis-refactor/quickstart.md`


## Phase 8: Strict FP, Typing, and No-Exception Gates (P1)

**Purpose**: Make the FP migration enforceable: typed immutable data, pure functions, Result-only recoverable failures, and no exception-driven domain flow.

- [X] T096 [P] Add static typing configuration or tighten existing type-check settings for migrated modules in `pyproject.toml`
- [X] T097 [P] Add architecture guardrail that public pipeline stage signatures are typed, use `Option` for optional domain values, and avoid unexplained `Any` in `tests/architecture/test_typed_stage_interfaces.py`
- [X] T098 [P] Add architecture guardrail that migrated domain models are frozen/immutable at stage boundaries in `tests/architecture/test_typed_immutable_models.py`
- [X] T099 [P] Add architecture guardrail that recoverable domain code does not raise/catch broad exceptions for control flow in `tests/architecture/test_no_exception_driven_domain_flow.py`
- [X] T100 Define typed frozen domain-model conventions and examples in `specs/007-functional-core-rop-ibis-refactor/data-model.md`
- [X] T101 Define allowed exception boundary policy and examples in `specs/007-functional-core-rop-ibis-refactor/contracts/pipeline-contract.md`
- [X] T102 Add typed stage protocol examples for total pure functions and fallible Result stages in `tests/examples/test_typed_pipeline_stage_example.py`
- [X] T103 Add tests proving boundary-local mutation cannot leak through pure immutable interfaces in `tests/unit/core/test_boundary_local_mutation.py`
- [X] T104 Audit migrated core modules for untyped public interfaces and record fixes in `specs/007-functional-core-rop-ibis-refactor/architecture-review.md`
- [X] T105 Audit migrated flows for exception-to-Result conversion boundaries and record findings in `specs/007-functional-core-rop-ibis-refactor/architecture-review.md`
- [X] T106 Add CI validation for type checks, typed-stage guardrails, immutable-model guardrails, and no-exception-flow guardrails in `scripts/validate_functional_ibis_refactor.py`
- [X] T107 Update the migration inventory schema to classify `untyped_interface`, `mutable_boundary_dto`, and `exception_flow` findings in `specs/007-functional-core-rop-ibis-refactor/data-model.md`
- [X] T108 Update maintainer review checklist with mandatory FP gates for purity, immutability, typing, and Result discipline in `specs/007-functional-core-rop-ibis-refactor/checklists/ambition-quality.md`
- [X] T109 Update final architecture review with pass/fail evidence for strict FP gates in `specs/007-functional-core-rop-ibis-refactor/architecture-review.md`


## Final Phase: Polish and Cross-Cutting Concerns

**Purpose**: Remove temporary paths, tighten guarantees, and complete migration evidence.

- [X] T110 Remove unused legacy SQL helpers made unreachable by Ibis paths in `src/ppi/storage/legacy_sql.py`
- [X] T111 Remove temporary feature flags for dual legacy/Ibis query execution in `src/ppi/query/pipeline.py`
- [X] T112 Normalize module imports and public exports for new core primitives in `src/ppi/core/__init__.py`
- [X] T113 Run and record final migration inventory evidence with zero unapproved read/query/analytics SQL in `specs/007-functional-core-rop-ibis-refactor/architecture-review.md`
- [X] T114 Run and record final query-family coverage evidence in `specs/007-functional-core-rop-ibis-refactor/architecture-review.md`
- [X] T115 Run and record public behavior compatibility evidence in `specs/007-functional-core-rop-ibis-refactor/architecture-review.md`
- [X] T116 Run and record performance smoke comparison evidence for representative query families in `specs/007-functional-core-rop-ibis-refactor/architecture-review.md`
- [X] T117 Update package-level architecture overview after migration in `specs/007-functional-core-rop-ibis-refactor/architecture-review.md`
- [X] T118 Update `specs/007-functional-core-rop-ibis-refactor/architecture-review.md` with final pass/fail status and remaining justified exceptions
- [X] T119 Audit write, ingestion, bulk import/export, schema, migration, lock, transaction, and maintenance DuckDB interactions for Ibis/backend-abstraction eligibility in `specs/007-functional-core-rop-ibis-refactor/architecture-review.md`
- [X] T120 Record approved non-Ibis DuckDB boundary exceptions with owner, rationale, tests, and re-evaluation condition in `specs/007-functional-core-rop-ibis-refactor/architecture-review.md`

## Dependencies

### Phase Dependencies

1. Phase 1 Setup must complete before Phase 2 Foundation.
2. Phase 2 Foundation blocks all story phases because guardrails, `Result`, pipeline primitives, and inventory validation are required.
3. US3 should start before or alongside US2 because Ibis read/query boundaries influence query pipeline shape.
4. US2 depends on Phase 2 and can proceed in parallel with later US3 query-family migrations once shared boundaries exist.
5. US1 compatibility tests should be established before removing legacy paths in US3 and before replacing orchestration in US2.
6. US4 depends on `DomainError`, `Result`, storage boundaries, and at least one migrated CLI/server path.
7. US5 depends on stable patterns from US2 and US3.
8. Strict FP/typing gates depend on Phase 2 and should run before final polish.
9. Final polish depends on all story phases and strict FP/typing gates, and uses the final evidence tasks T110-T120.

### Story Dependencies

| Story | Depends on | Reason |
|---|---|---|
| US3 | Phase 2 | Needs inventory, guardrails, Ibis backend, and golden tooling |
| US2 | Phase 2, partial US3 | Needs `Result`, pipeline primitives, immutable models, and storage boundaries |
| US1 | Phase 2, US2, US3 | Validates public behavior after internals are redirected |
| US4 | Phase 2, US2, US3 | Needs real migrated flows to standardize errors |
| US5 | US2, US3, US4 | Documents and enforces final patterns |
| Strict FP Gates | Phase 2, US2, US3 | Validates typed immutable data, pure stages, and no exception-driven recoverable flow |

## Parallel Execution Examples

After Phase 2 completes:

```text
# Parallel US3 work
T024 duckdb boundary
T028 query contract models
T033 read model mappers
T034 golden utilities
```

```text
# Parallel US2 pure-stage work
T049 frozen models
T051 validation stages
T053 normalization stages
T054 metric stages
T055 write-prep stages
```

```text
# Parallel US4 rendering work after DomainError exists
T076 CLI error renderer
T077 RPC/server error mapper
T086 CLI renderer tests
T087 server mapper tests
```

## MVP Scope

The MVP is not “all polish”; it is the smallest slice that proves the architecture is real and not cosmetic:

1. Phase 1 Setup: T001-T006.
2. Phase 2 Foundation: T007-T023.
3. US3 first vertical slice: T024-T030, T033-T036, T039-T040, T043-T044, T047-T048.
4. US2 first vertical slice: T049-T057 plus T059-T064.
5. US1 minimum compatibility: T066-T069 and T074.
6. Strict FP gate slice: T096-T104, so typed interfaces, immutable DTOs, and no-exception-flow checks are present before declaring MVP architecture proof.

MVP completion criteria:

- at least one real query family is fully Ibis-migrated with golden parity and legacy SQL removed;
- at least one real analyze/history workflow is stage-composed with `Result` short-circuiting and typed immutable stage-boundary data;
- guardrails reject new raw analytical SQL outside approved boundaries;
- guardrails reject untyped stage interfaces, mutable stage-boundary DTOs, and exception-driven recoverable domain flow;
- public CLI behavior remains compatible for the migrated slice.

## Implementation Strategy

1. **Inventory first**: Do not refactor blindly. Every SQL/DuckDB finding and every query family needs a disposition before broad edits.
2. **Guardrails before migration**: Add failing tests early so new raw SQL does not enter while migration is ongoing.
3. **Vertical slices over broad rewrites**: Migrate one query family end-to-end: inventory -> Ibis builder -> execution -> mapper -> golden parity -> remove legacy path.
4. **Pipeline slices over helper extraction**: Convert one workflow end-to-end: validate -> boundary -> normalize -> compute -> write/execute -> render.
5. **Remove dual paths quickly**: Do not keep permanent legacy SQL and Ibis implementations side by side.
6. **Enforce typed FP gates**: A migrated area is incomplete if public stage/builder signatures are untyped, stage-boundary data is mutable, or recoverable domain failures use exceptions.
7. **Document exceptions with evidence**: Any direct DuckDB usage that remains must have inventory, owner, reason, and tests.

## Format Validation

- Total tasks: 120
- All tasks use checkbox format.
- All tasks have stable IDs.
- All story tasks include `[USn]` labels.
- Setup, foundation, and polish tasks do not use story labels.
- Every task names at least one concrete file path.
- Parallel tasks are marked `[P]` only when they touch independent files and can proceed after phase prerequisites.
