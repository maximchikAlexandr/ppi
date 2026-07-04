# Requirements Quality Checklist: Spec 007 Ambition, ROP, Ibis, and FP Strictness

**Feature**: `007-functional-core-rop-ibis-refactor`  
**Created**: 2026-07-03  
**Focus**: Full-spec quality audit for an ambitious, non-cosmetic functional core / ROP / Ibis-first refactor.  
**Last Revalidated**: 2026-07-04 after switching active Spec Kit context to 007.

## Ambition and Scope

- [x] **CHK001**: Is the specification explicit that this is an architectural migration rather than cosmetic helper extraction? [Spec §Ambition Standard]
- [x] **CHK002**: Are all documented PPI public surfaces in scope or explicitly dispositioned? [Spec §FR-001, §FR-025]
- [x] **CHK003**: Does the spec prevent a single proof-of-concept migration from being presented as sufficient completion? [Spec §FR-025, §SC-009]
- [x] **CHK004**: Are temporary dual legacy/Ibis paths required to have removal conditions and final disposition? [Spec §FR-024, §SC-011]

## Functional Core and ROP

- [x] **CHK005**: Are requirements clear that core domain transformations are pure and cannot read hidden runtime state? [Spec §FR-002]
- [x] **CHK006**: Are side-effect boundaries named and separated from pure stages? [Spec §FR-003, Plan §Architecture Principles]
- [x] **CHK007**: Are recoverable failures required to use `Result[T, DomainError]` instead of exceptions, `None`, sentinels, booleans, or ad-hoc dictionaries? [Spec §FR-005]
- [x] **CHK008**: Is the distinction between recoverable domain errors and programmer defects objectively testable? [Spec §FR-006, Pipeline Contract §Result Discipline]
- [x] **CHK009**: Are diagnostics required to include stage-level context and stable machine-readable error data? [Spec §FR-016, Public Behavior Contract]
- [x] **CHK022**: Is the canonical algebraic type provider unambiguous: `Expression` `Result`/`Option`, `Ok`, `Error`, `Some`, and `Nothing`, with no second custom Result/Option representation? [Spec §Clarifications, §FR-005, §FR-005A; Research §Decision 1]
- [x] **CHK023**: Are optional domain values required to use `Option` instead of `None` inside migrated core/query/pipeline stages? [Spec §FR-005A, Pipeline Contract §Stage Contract]

## Typed Immutability

- [x] **CHK010**: Are typed immutable structures mandatory at stage boundaries? [Spec §FR-004, §FR-007]
- [x] **CHK011**: Are performance exceptions for boundary-local mutation constrained and unobservable to callers? [Spec §FR-007, §FR-018]
- [x] **CHK012**: Are untyped public stage/builder interfaces and unexplained `Any` usage rejected for migrated modules? [Spec §FR-021, §SC-010]

## Ibis-First Data Access

- [x] **CHK013**: Is Ibis the default for read/query/analytical transformations, with direct DuckDB limited to named infrastructure boundaries? [Spec §FR-010, §FR-011]
- [x] **CHK014**: Are pure/lazy Ibis expression builders prohibited from executing, opening connections, compiling raw SQL, or materializing results? [Spec §FR-011B]
- [x] **CHK015**: Does the spec reject moving raw SQL into helpers as a workaround? [Spec §FR-011A, Data Access Contract §Prohibited Patterns]
- [x] **CHK016**: Are all remaining DuckDB/raw SQL usages required to be inventoried with owner, reason, tests, and future status? [Spec §FR-009, §FR-023, §SC-003]
- [x] **CHK017**: Are query-family parity checks measured by columns, serialized types, row counts, values, nulls, ordering, and error behavior? [Spec §SC-005, Data Access Contract §Golden Test Contract]

## Enforcement and Evidence

- [x] **CHK018**: Are executable guardrails required instead of relying only on documentation or code review? [Spec §FR-026, §SC-012]
- [x] **CHK019**: Are final acceptance criteria tied to named evidence artifacts and commands? [Spec §FR-030, §SC-012]
- [x] **CHK020**: Are task dependencies consistent with the requirement that strict FP gates run before final polish? [Tasks §Dependencies]
- [x] **CHK021**: Are non-query DuckDB interactions such as writes, ingestion, schema/migrations, locks, transactions, and maintenance explicitly dispositioned rather than silently excluded from the Ibis migration ambition? [Spec §FR-031, Plan §Wave 0.6]
- [x] **CHK024**: Is the validation entrypoint unambiguous, with inventory, guardrail, golden, performance, typing, immutability, result-flow, and Ibis checks routed through `scripts/validate_functional_ibis_refactor.py`? [Tasks §T002, §T094; Quickstart §Step 2, §Step 6, §Step 7]

## Usage

Use this checklist before implementation starts, after each major migration slice, and before final architecture review. Failed items block implementation handoff until the related requirement, task, or evidence artifact is tightened.

## Revalidation Notes

All items pass after context switch cleanup. The active Spec Kit feature pointer,
AGENTS.md project context, requirements checklist, ambition checklist, plan,
tasks, and public behavior contract now consistently target Spec 007.
