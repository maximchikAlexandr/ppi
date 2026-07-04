# Quickstart: Validate Spec 007 Functional Core, ROP, Typed Immutable Data & Ibis-First Refactor

**Feature**: `007-functional-core-rop-ibis-refactor`

This quickstart is for contributors implementing or reviewing the refactor.

## Prerequisites

- Python development environment for PPI.
- Project dependencies installed, including DuckDB and Ibis DuckDB backend when added by the implementation.
- Fixture repositories and fixture `.ppi/history.duckdb` stores for golden-output comparison.
- Access to the current baseline branch to compare legacy query outputs during migration.

## Step 1: Establish baseline

Run the existing tests before changing behavior:

```bash
python -m pytest
```

Run smoke commands against a representative repository:

```bash
ppi doctor <repo>
ppi analyze <repo>
ppi query <repo> --help
```

If `serve` or `rpc` is supported in the current project state, smoke-test those paths too.

## Step 2: Build migration inventory

Scan for direct DuckDB/raw SQL usage through the canonical validation entrypoint:

```bash
python scripts/validate_functional_ibis_refactor.py --inventory
```

Expected outcome:

- every direct `duckdb` import or connection execution is listed;
- every raw analytical SQL string is listed;
- each entry is classified as Ibis migration target, approved DuckDB boundary, test fixture, or false positive.


## Step 2.5: Build query-family disposition table

After the raw grep inventory, create a query-family table. It must cover CLI metrics, RPC methods, dashboard tab datasets, server handlers, and history read-model consumers.

Each row must answer:

- where is the current query implemented?
- which public surface consumes it?
- what tables/columns does it read?
- what output contract must remain stable?
- what is the Ibis expression builder name?
- what golden fixture proves parity?
- when is the legacy SQL path removed?

Expected outcome: no read/query family has status `unknown`.

## Step 3: Validate foundation abstractions

Run unit tests for:

- `Expression` `Result`, `Ok`, `Error`, `Option`, `Some`, and `Nothing`, plus project helpers such as `bind`, `map`, and `map_error`;
- `DomainError` code/category/message/stage behavior;
- pipeline stage short-circuiting;
- error renderer output in text and JSON/RPC modes.

Expected outcome:

- recoverable failures compose as `Error` values;
- optional domain absence composes as `Option` values, not `None`;
- unexpected programmer errors are not hidden as normal domain failures;
- rendered machine errors include stable `code` and `message`.

## Step 4: Validate Ibis query migration

For each migrated query family:

1. Run the legacy query against fixture store.
2. Run the Ibis expression path against the same fixture store.
3. Compare public output.

Expected comparison dimensions:

- columns and public field names;
- serialized types;
- row counts;
- numeric values;
- null handling;
- ordering where guaranteed;
- error behavior for invalid params or missing store.

## Step 5: Validate public behavior

Run compatibility checks:

```bash
python -m pytest tests
ppi doctor <repo>
ppi analyze <repo>
ppi query <repo> <representative-query>
```

For machine-readable modes, verify error shape:

```json
{
  "ok": false,
  "error": {
    "code": "...",
    "message": "..."
  }
}
```

## Step 6: Validate architecture guardrails

Run guardrail checks through the canonical validation entrypoint:

```bash
python scripts/validate_functional_ibis_refactor.py --guardrails
```

Expected outcome:

- no direct `duckdb` imports outside approved boundary/test modules;
- no raw analytical SQL construction outside approved boundary/test modules;
- no new query code without Ibis expression tests or inventory exception;
- pure stages do not import IO/database/server modules.

## Step 7: Validate performance

Run smoke/performance scenarios for small, medium, and large repositories:

```bash
python scripts/validate_functional_ibis_refactor.py --performance --fixture small
python scripts/validate_functional_ibis_refactor.py --performance --fixture medium
python scripts/validate_functional_ibis_refactor.py --performance --fixture large
```

Expected outcome:

- runtime remains within the accepted threshold from the spec unless a decision-log tradeoff is recorded;
- Ibis paths do not eagerly materialize large tables unnecessarily;
- dashboard/query paths remain responsive.

## Done Criteria

A refactor slice is ready for review when:

- all tests pass;
- touched direct DuckDB/SQL usage is inventoried;
- migrated query families have golden-output evidence;
- public behavior remains compatible;
- no unapproved raw analytical SQL remains in the touched read/query path;
- docs or examples show the correct pipeline/Ibis pattern for future work.


## Strict FP validation

Expected final validation must include:

```bash
python scripts/validate_functional_ibis_refactor.py --typing --immutability --result-flow --ibis --golden
```

The validation should fail when migrated code contains untyped public stage/builder signatures, mutable stage-boundary DTOs, recoverable failure via exceptions, or unapproved raw SQL/DuckDB calls.
