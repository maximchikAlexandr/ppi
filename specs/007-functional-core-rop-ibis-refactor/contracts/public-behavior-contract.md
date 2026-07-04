# Contract: Public Behavior Compatibility

**Feature**: `007-functional-core-rop-ibis-refactor`

## Purpose

Ensure internal refactoring does not unintentionally change user-facing behavior.

## Compatibility Surfaces

The following surfaces must remain compatible unless an explicit migration note is accepted:

- CLI text output for documented commands;
- CLI JSON output mode where supported;
- `query` command output;
- `rpc` request/response behavior where supported;
- `serve`/dashboard data access behavior;
- VS Code bridge/dashboard response shapes where applicable;
- existing `.ppi/history.duckdb` stores.

## CLI Contract

For commands such as `doctor`, `analyze`, `query`, `serve`, and `rpc`:

- accepted arguments and common options remain compatible;
- success/failure exit semantics remain compatible;
- text output remains readable and actionable;
- JSON/machine output preserves stable field names and error fields;
- debug mode may reveal richer cause details, but default mode must not regress into stack traces for recoverable failures.

## Query/RPC/Dashboard Contract

For each query family or endpoint:

- response field names remain compatible;
- null semantics remain compatible;
- numeric values remain compatible within accepted tolerances;
- ordering remains compatible where callers rely on ordering;
- read-only requests must not mutate the history store or acquire writer locks;
- internal Ibis/DuckDB details must not leak into public responses.

## Existing Store Contract

Existing `.ppi/history.duckdb` stores must remain readable when they are compatible with the current application schema. If a schema migration is required, it must be explicit, reversible where practical, and documented outside this refactor plan.

## Regression Evidence

Each touched public surface must have one of:

- existing automated test coverage preserved;
- new compatibility test;
- golden-output fixture comparison;
- documented manual smoke test in `quickstart.md` for cases not yet automated.
