# Research: Spec 007: Functional Core, Railway Oriented Programming & Ibis-First Refactor

**Feature**: `007-functional-core-rop-ibis-refactor`  
**Date**: 2026-07-03

## Decision 1: Standardize on the existing Expression Result

**Decision**: Standardize migrated code on the existing `Expression` dependency: `expression.Result` is the canonical result type, `Ok(...)` represents success, and `Error(...)` represents recoverable failure. `expression.Option`, `Some(...)`, and `Nothing` are the canonical representation for optional domain values. `src/ppi/core/result.py` may provide project-local aliases/combinators (`map`, `bind`, `map_error`, `tap`, `recover`, `collect`) and stage-context helpers, but it must wrap or re-export `Expression` primitives rather than creating a second incompatible result or option type.

**Rationale**: The project already depends on `Expression` and current Python code already uses `Result`, `Ok`, and `Error`. Reusing that representation satisfies the constitution's typed `Result`/`Option` rule, avoids duplicate failure/absence models, and still leaves room for PPI-specific helper functions and `DomainError` semantics.

**Alternatives considered**:

- Use exceptions only: rejected because it does not satisfy result-based recoverable error composition.
- Create a new project-owned Result implementation: rejected because it would duplicate the existing `Expression` dependency and split result semantics.
- Use tuple conventions like `(value, error)`: rejected because it is weaker for typing, composition, and maintainability.

## Decision 2: Treat Ibis expression builders as pure query descriptions

**Decision**: Query functions should build Ibis expressions without executing them. Execution belongs in a backend adapter that binds DuckDB/Ibis connections and converts external failures to `Result` errors.

**Rationale**: This preserves functional purity in query construction, makes expressions easier to test, and keeps IO/backend concerns isolated. It also allows expression-level tests and golden-output execution tests to be separated.

**Alternatives considered**:

- Execute Ibis expressions directly inside every query handler: rejected because it mixes pure query definition with IO.
- Keep raw SQL builders and only wrap execution: rejected because the target is Ibis-first read/query code.
- Hide Ibis entirely behind generic repositories: partially useful for callers, but implementation still needs tested expression factories.

## Decision 3: Keep direct DuckDB for schema/write/lock mechanics in the first wave

**Decision**: Do not force Ibis into schema migrations, file management, transaction control, locking, pragmas, or write mechanics where direct DuckDB APIs are safer or clearer. Keep those operations in `DuckDB Boundary` modules with inventory records.

**Rationale**: The requested migration targets Python code interacting with DuckDB, especially raw analytical SQL. However, replacing all backend mechanics would risk correctness and storage compatibility. A narrow boundary allows maximum useful migration without destabilizing persistence.

**Alternatives considered**:

- Replace all DuckDB API usage immediately: rejected as too risky for schema, lock, and transaction semantics.
- Leave storage and query layers unchanged: rejected because it does not satisfy the Ibis-first migration goal.
- Replace DuckDB storage engine: out of scope for this feature.

## Decision 4: Inventory before migration is mandatory

**Decision**: Before replacing query code broadly, create a migration inventory of direct DuckDB usage, SQL strings, and database-shaped helpers. The inventory becomes a tracked artifact used by tasks, tests, and review gates.

**Rationale**: The goal is maximum practical migration, so success depends on knowing every direct usage site. Without inventory, hidden raw SQL can remain and the migration cannot be measured.

**Alternatives considered**:

- Migrate only obvious modules first: useful but incomplete and likely to miss hidden SQL.
- Depend only on code review: insufficient for a codebase-level style migration.
- Block all SQL instantly: too disruptive before classifying schema/write/test fixtures.

## Decision 5: Golden-output tests are the primary safety net for Ibis migration

**Decision**: For each migrated query family, compare legacy and Ibis outputs on representative fixture stores before removing the legacy path.

**Rationale**: Ibis may differ in type coercion, ordering, null handling, timestamp behavior, or aggregate semantics. Golden tests give direct evidence that public behavior remains compatible.

**Alternatives considered**:

- Trust unit tests of expressions only: insufficient because backend execution behavior matters.
- Compare only row counts: insufficient because columns, types, ordering, and values can drift.
- Remove legacy queries first: risky and makes behavior comparison harder.

## Decision 6: Architecture guardrails should be automated

**Decision**: Add tests or scripts that fail on new direct `duckdb` imports, `.execute()` raw analytical SQL, or SQL string construction outside approved boundary/test modules.

**Rationale**: The clarified goal prohibits parallel long-term raw SQL style. Automated guardrails prevent regression after initial migration.

**Alternatives considered**:

- Rely on maintainers reading documentation: insufficient.
- Ban `.execute()` globally: too broad because boundary modules and non-SQL use may be valid.
- Use heavyweight static analysis first: maybe later, but simple repository scans can enforce the first contract quickly.
