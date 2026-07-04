# Specification Analysis Report

| ID | Category | Severity | Location(s) | Summary | Recommendation | Status |
|----|----------|----------|-------------|---------|----------------|--------|
| A001 | Task ordering | HIGH | `tasks.md` Phase 8, Final Phase | Strict FP gates must run before final polish and final evidence. | Keep strict FP gates before final polish and make MVP include a strict gate slice. | Resolved: T096-T109 precede T110-T120. |
| A002 | Checklist quality | MEDIUM | `checklists/requirements.md`, `checklists/ambition-quality.md` | Implementation needs requirement-quality questions with global IDs, not only status ticks. | Use traceable CHK items for ambition, FP/ROP, typed immutability, Ibis, DuckDB boundaries, and evidence. | Resolved: CHK001-CHK021. |
| A003 | Ambition enforceability | HIGH | `spec.md`, `plan.md` | The spec must not be satisfiable by a single Ibis example, wrappers, or helper extraction. | Keep non-cosmetic ambition standard, surface-complete inventory, vertical-slice obligations, and executable evidence as core requirements. | Resolved in core sections. |
| A004 | Query-family coverage | HIGH | `spec.md`, `plan.md`, `tasks.md` | Query-family inventory must be tied to documented public surfaces and cannot keep `unknown` disposition. | Require 100% named query-family disposition and golden parity/removal conditions. | Resolved by FR-023/024/025, SC-003/005/009/011, T021-T022, T114. |
| A005 | Evidence discipline | MEDIUM | `spec.md`, `plan.md`, `tasks.md` | Final acceptance must depend on executable evidence, not prose. | Require guardrail commands, golden-output reports, type-check output, inventory validation, and final architecture review. | Resolved by FR-026/030, SC-012, T106, T113-T120. |
| A006 | Full DuckDB interaction scope | HIGH | `spec.md`, `plan.md`, `tasks.md` | The original ambition mentions maximum migration of Python code interacting with DuckDB; read/query focus alone can leave writes/bulk/schema paths silently excluded. | Require explicit disposition for writes, ingestion, bulk import/export, schema/migrations, locks, transactions, maintenance, tests, and false positives; prefer Ibis/backend abstraction where safe and isolate remaining direct DuckDB usage. | Resolved by FR-009/011/031, SC-013, Plan Wave 0.6, T119-T120, CHK021. |
| A007 | Result/Option ambiguity | HIGH | `spec.md`, `research.md`, `plan.md`, `tasks.md`, `contracts/pipeline-contract.md`, `data-model.md` | A weaker implementer could create a second local Result type or keep `None` as a domain absence protocol despite the existing `Expression` dependency and constitution. | Make `Expression` the canonical provider: `Result`, `Ok`, `Error`, `Option`, `Some`, and `Nothing`; allow local helpers only as wrappers/re-exports. | Resolved by FR-005/FR-005A, Research Decision 1, T007/T011/T097, Pipeline Contract, Data Model Option entity, CHK022-CHK023. |
| A008 | Validation entrypoint ambiguity | MEDIUM | `quickstart.md`, `tasks.md` | Quickstart referenced separate validation scripts not represented as canonical implementation tasks. | Route inventory, guardrail, golden, performance, typing, immutability, result-flow, and Ibis checks through `scripts/validate_functional_ibis_refactor.py`. | Resolved by T002/T094 and quickstart command updates; CHK024 added. |

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 Public behavior compatibility | Yes | T006, T065-T075, T115 | Covered by smoke/golden/public reports. |
| FR-002 Pure functional core | Yes | T009, T049-T064, T096-T109 | Covered by pipeline primitives, migration slices, and strict FP gates. |
| FR-003 Side-effect boundaries | Yes | T024, T050, T075, T080-T082 | Boundary and error mapping tasks cover this. |
| FR-004 Explicit typed pipelines | Yes | T009, T049-T064, T096-T104 | MVP requires typed pipeline slice, not helper-only refactor. |
| FR-005 Result-based recoverable errors | Yes | T007-T013, T076-T087, T101, T105 | Uses `Expression` `Result`, `Ok`, and `Error`; no second Result type. |
| FR-005A Option-based domain absence | Yes | T007, T011, T097 | Uses `Expression` `Option`, `Some`, and `Nothing`; `None` is boundary-only. |
| FR-009/FR-010 Ibis-first migration inventory | Yes | T018-T022, T029-T048, T107, T113-T114 | Tied to public surfaces and query families. |
| FR-021/FR-022 Typing and guardrails | Yes | T096-T106 | Executable guardrails required. |
| FR-023 Surface-aware inventory | Yes | T020-T022, T114 | Includes surface, owner/module, target, disposition, evidence. |
| FR-024 Dual-path removal | Yes | T041-T048, T110-T111 | Legacy/Ibis parallel paths require removal conditions. |
| FR-025 P1 vertical slices | Yes | MVP Scope, T024-T075, T096-T104 | Prevents proof-of-concept-only delivery. |
| FR-030 Final architecture evidence | Yes | T118 | Final pass/fail evidence retained. |
| FR-031 Non-query DuckDB disposition | Yes | T020, T024-T025, T119-T120 | Prevents silent exclusion of writes/bulk/schema/lock/transaction/maintenance paths. |

## Constitution Alignment Issues

No constitution conflicts remain. The project constitution exists at `.specify/memory/constitution.md`; Spec 007 now explicitly aligns with Functional Core/Object-Oriented Shell, Layered Core Independence, Plugin/Fact Contracts, Single-Writer Data Ownership, and Typed Contracts & Explicit Error Handling. The previous stale plan statement that no constitution existed was corrected.

## Unmapped Tasks

No blocking unmapped implementation tasks remain. Setup, foundation, guardrail, and final-evidence tasks are intentionally cross-cutting and not mapped to a single user story.

## Metrics

- Total Requirements: 32 functional requirements, counting FR-005A as the added Option/absence rule
- Total Tasks: 120 implementation tasks
- Coverage %: 100% for stated functional requirements at task-family level
- Ambiguity Count: 0 blocking ambiguity markers
- Duplication Count: 0 duplicate task IDs after excluding illustrative examples
- Critical Issues Count: 0 after integrated hardening

## Next Actions

Implementation should start with Phase 1 and Phase 2 only after validating `checklists/ambition-quality.md`. The first implementation milestone is the MVP vertical slice: one real Ibis query-family migration, one real functional analyze/history pipeline slice, public compatibility tests, and strict FP gates.
