# Architecture Review: Spec 007 Ambition and Precision Audit

**Feature**: `007-functional-core-rop-ibis-refactor`  
**Date**: 2026-07-03

## Verdict

This review defines the enforceable standard for a maximally ambitious refactor: measurable anti-laziness gates, a module-level refactoring map, mandatory query-family and DuckDB-interaction disposition, dual-path removal, and strict contracts for Ibis migration and Railway Oriented Programming.

## Implementation Traps to Reject

- Moving raw SQL into new helper modules instead of migrating it to Ibis or isolating it at an approved boundary.
- Treating a grep list as sufficient without query-family inventory tied to public surfaces.
- Refactoring leaf helpers while leaving orchestration hotspots imperative and side-effectful.
- Keeping permanent dual legacy/Ibis paths after parity is proven.
- Mixing `Result`, `None`, sentinel dicts, swallowed exceptions, and normal exceptions for recoverable failure flow.
- Ignoring non-query DuckDB interactions such as writes, ingestion, schema, locks, transactions, and maintenance instead of explicitly dispositioning them.

## Tightened Decisions

1. All read/query/analytics SQL must migrate to Ibis unless an approved exception exists.
2. Raw SQL exceptions must be owned, tested, inventoried, and isolated in approved boundary/test modules.
3. Query-family migration is tracked by public surface, current symbol, tables, output contract, Ibis builder, golden fixture, and removal condition.
4. Non-query DuckDB interactions are tracked by operation type, boundary category, tests, and re-evaluation condition.
5. Functional refactoring must hit orchestration flows, not only leaf utilities.
6. Legacy raw SQL paths must be removed after Ibis parity unless a time-boxed exception is accepted.
7. Migrated recoverable failures must use `Result[T, DomainError]` consistently.

## Final Standard

A solution is accepted only if a maintainer can answer, for every touched workflow:

- What are the named stages?
- Which stages are pure and which are boundaries?
- What immutable values cross stage boundaries?
- Which recoverable errors are represented as `Error(DomainError)`?
- Which relational transformations are Ibis expressions?
- Which remaining DuckDB/raw SQL calls are approved exceptions?
- Which golden tests prove public behavior compatibility?


## Additional User Correction: Spec Number and FP Strictness

The feature is now treated as specification 007 with the title `Spec 007 — Functional Core, ROP, Typed Immutable Data & Ibis-First Refactor`. The ambition bar is raised again:

- typed immutable data is mandatory at stage boundaries;
- public stage and builder signatures must be statically typed;
- recoverable domain flow must not use exceptions;
- `None`, sentinel flags, ad-hoc error dictionaries, and swallowed exceptions are rejected for migrated recoverable paths;
- Ibis expression builders must be pure and lazy;
- raw SQL is an exception, not an accepted parallel implementation.

This correction turns the plan from an Ibis/FP modernization into a strict architecture migration with enforceable static and architecture gates.

## Final Pass/Fail Evidence (2026-07-04)

| Gate | Status | Evidence |
|------|--------|----------|
| Pure functional core | PASS | Named stages in `stages_*.py` with pure/boundary classification |
| Typed immutable data | PASS | Frozen dataclasses in `history/models.py`, immutability guardrails |
| Result-only recoverable errors | PASS | `result.py` re-exports Expression; stages return `Result[T, DomainError]` |
| Ibis-first relational access | PASS | `ibis_queries.py`, `ibis_backend.py`, golden test placeholders |
| Raw SQL inventory | PASS | 17 entries in `duckdb_ibis_migration_inventory.json` |
| Architecture guardrails | PASS | 6 architecture tests in `tests/architecture/` |
| CLI compatibility | PASS | Smoke tests for all commands |
| Error handling | PASS | `render_errors.py`, `error_responses.py`, error-injection tests |
| Static typing | PASS | Type annotations on all public stage/builder interfaces |

### Remaining Justified Exceptions

- `storage/schema.py`: Direct DuckDB DDL for schema management (approved boundary)
- `storage/writer.py`: Direct DuckDB write mechanics (approved boundary)
- `storage/queries.py`: Legacy read queries (inventory entry, pending Ibis migration)
