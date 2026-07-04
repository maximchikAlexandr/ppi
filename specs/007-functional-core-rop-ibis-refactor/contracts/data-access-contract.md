# Contract: Ibis-First Data Access, Typed Query Builders, and DuckDB Boundary

**Feature**: `007-functional-core-rop-ibis-refactor`

## Purpose

Define how Python code may interact with relational history data after the refactor.

## Default Rule

Read/query/analytical transformations must be implemented as Ibis expressions/functions. Direct raw analytical SQL in business logic is not allowed.

## Ibis Expression Builder Contract

An expression builder must:

- accept validated immutable parameters;
- receive table bindings or a typed table registry;
- build and return a lazy Ibis expression;
- not execute the expression;
- not open DuckDB connections;
- not construct raw SQL strings;
- document expected output fields and ordering guarantees where relevant.

Example shape:

```text
build_<query_family>_expr(tables, params) -> IbisQueryExpression
```

## Ibis Execution Boundary Contract

The execution boundary may:

- bind Ibis to the DuckDB backend;
- load table references for the existing history store;
- execute Ibis expressions;
- convert backend errors into `DomainError` values;
- materialize only the result needed by the public contract.

The execution boundary must not contain business-specific raw SQL as a shortcut.

## DuckDB Boundary Contract

Direct DuckDB usage is allowed only for approved boundary categories:

- connection lifecycle;
- storage file management;
- schema initialization and migrations;
- transaction/locking semantics;
- pragmas/maintenance;
- write or bulk mechanics not safely expressible via Ibis;
- proven unsupported Ibis feature with inventory record.

Any remaining direct DuckDB usage must be recorded in the migration inventory.


## Required Query Migration Pattern

Every migrated read/query family must follow this shape:

```text
validate_request(raw_input)
  -> Result[ImmutableParams, DomainError]
  -> build_<family>_expr(tables, params)
  -> Result[IbisExpression, DomainError]
  -> execute_expr(expr, backend_context)
  -> Result[TabularResult, DomainError]
  -> map_to_public_contract(tabular_result)
  -> Result[PublicDTO, DomainError]
```

The expression builder is the center of the migration. A change that merely moves raw SQL into another helper does not satisfy this contract.

## Approved Raw SQL / DuckDB Exceptions

An exception is valid only when all are true:

1. It is inside an approved boundary module or test fixture.
2. It has a migration inventory record.
3. The record names the Ibis limitation, transactional requirement, schema/write requirement, or measured performance reason.
4. It has tests proving public behavior or storage safety.
5. It has an owner and revisit decision.

Unowned or unexplained SQL is not an exception; it is remaining migration work.

## Review Checklist for Each Query Family

- [ ] No raw analytical SQL remains on the normal path.
- [ ] Ibis expression builder has unit tests.
- [ ] Ibis execution has fixture/golden parity tests.
- [ ] Nulls, ordering, numeric precision, timestamp handling, and serialization were checked.
- [ ] Public caller contract did not change unless separately accepted.
- [ ] Legacy SQL path was removed or explicitly time-boxed.

## Migration Inventory Contract

Every direct DuckDB or raw SQL finding must be represented as:

```json
{
  "id": "MI-001",
  "module": "src/ppi/...",
  "symbol": "function_or_class",
  "usage_type": "read_query|analytics|write|schema|transaction|lock|maintenance|test_fixture|false_positive",
  "current_pattern": "raw_sql|duckdb_execute|duckdb_connection|query_helper",
  "target_pattern": "ibis_expression|duckdb_boundary|remove|no_change_false_positive",
  "status": "discovered|in_progress|migrated|approved_exception|removed",
  "reason": "required for exceptions",
  "tests": ["test reference"]
}
```

## Golden Test Contract

Each migrated query family must prove compatibility by comparing:

- column names;
- data types or serialized public types;
- row counts;
- values and numeric tolerances;
- null handling;
- ordering where guaranteed;
- user-facing error behavior.

## Prohibited Patterns

- raw analytical SQL strings in `query`, `server`, `cli`, or domain workflow modules;
- `.execute("select ...")` in read/query business logic;
- building SQL by f-string/string concatenation for analytical queries;
- Ibis expression execution inside pure expression-builder functions;
- untracked DuckDB exceptions.


## Raw SQL Elimination Standard

For normal read/query/analytics paths, the accepted target is zero raw SQL construction. The following patterns fail review unless they are inside an approved boundary/test fixture with an inventory exception:

- SQL fragments such as `SELECT`, `WITH`, `JOIN`, `GROUP BY`, `ORDER BY`, or aggregate expressions in Python strings;
- helper functions that return SQL text;
- functions that interpolate table/column names into SQL strings;
- direct `duckdb.execute(...)` or connection SQL calls for reads/analytics;
- materializing data early only to reproduce relational operations in Python loops.

Ibis expression builders must be typed pure functions. They may compose tables, columns, joins, filters, projections, aggregations, orderings, windows, and limits as lazy expressions, but must not execute or compile SQL as part of business logic.
