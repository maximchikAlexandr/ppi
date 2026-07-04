# Implementation Handoff: Spec 007

This file is the shortest authoritative route for an implementation agent. It does not replace `spec.md`, `plan.md`, or `tasks.md`; it tells the implementer how to read them without downgrading the ambition.

## Non-negotiable interpretation

Spec 007 is an architectural migration, not cleanup. Do not satisfy it by extracting helpers, wrapping legacy SQL, adding one Ibis proof of concept, or documenting exceptions without executable evidence.

The implementation must move PPI toward:

1. pure functional core;
2. explicit named pipelines;
3. typed immutable stage-boundary data;
4. `Result[T, DomainError]` for recoverable failures;
5. no exception-driven recoverable domain flow;
6. Ibis-first read/query/analytics logic;
7. explicit disposition of every direct DuckDB interaction, including writes, ingestion, bulk operations, schema/migration, locks, transactions, maintenance, tests, and false positives.

## Execution order

1. Complete Phase 1 and Phase 2 in `tasks.md` first. Do not start broad refactoring before `Result`, `DomainError`, pipeline primitives, inventory schema, and architecture guardrails exist.
2. Populate migration and query-family disposition evidence in `architecture-review.md` before migration.
3. Migrate by real vertical slices, not isolated helpers:
   - one Ibis query family end to end;
   - one functional analyze/history pipeline end to end;
   - compatibility/golden tests before legacy removal.
4. Run strict FP gates before final polish: T096-T109 must pass before T110-T120.
5. Final completion requires executable evidence in `architecture-review.md`, not prose-only claims.

## What blocks acceptance

- Any normal read/query/dashboard/RPC analytical path still builds raw SQL outside an approved boundary.
- Any migrated workflow remains a long imperative function with mixed validation, IO, transformation, DB access, and rendering.
- Any migrated recoverable flow uses exceptions, `None`, booleans, sentinel dictionaries, or swallowed exceptions instead of `Result`.
- Any public pipeline stage/builder interface is untyped or exposes mutable stage-boundary DTOs.
- Any direct DuckDB production usage is absent from the inventory.
- Any non-Ibis DuckDB usage lacks owner, rationale, tests, boundary category, and re-evaluation condition.

## Minimal MVP slice

The MVP is not “one helper converted.” It is:

- Phase 1 setup;
- Phase 2 foundation and guardrails;
- one query family migrated from legacy SQL/DuckDB to Ibis with golden parity and legacy-path removal condition;
- one analyze/history workflow converted into named typed pipeline stages;
- public compatibility tests for the touched CLI/RPC/dashboard surface;
- strict FP/typing/no-exception gates for the touched modules.
