# Specification Analysis Report

## Findings

| ID | Category | Severity | Location(s) | Summary | Remediation Applied |
|----|----------|----------|-------------|---------|---------------------|
| A01 | Path drift | CRITICAL | `tasks.md`, `spec.md`, `plan.md` | Tasks referenced `src/ppi/analysis`, `frontend/src/lib`, and `frontend/src/features`, which do not match the current repository path families described in source notes. A weaker implementation model could create parallel fake trees instead of refactoring existing code. | Replaced backend task targets with `src/ppi/core/pipelines`, `src/ppi/adapters`, `src/ppi/history/pipelines`, and `src/ppi/cli/*`; replaced frontend targets with `frontend/src/api`, `frontend/src/rop`, `frontend/src/transforms`, `frontend/src/pages`, and `frontend/src/components`; added path guardrails to spec, plan, tasks, quickstart, contracts, and checklist. |
| A02 | Phase ordering contradiction | HIGH | `plan.md` milestones vs old `tasks.md` phases | Plan and assumptions say Python history/effects should follow Python core work before frontend/VS Code polish, but old tasks placed history after frontend and VS Code. | Reordered tasks so Phase 5 is history/effects, Phase 6 is frontend, Phase 7 is VS Code; updated task IDs, dependencies, parallel examples, and story criteria. |
| A03 | Missing path-grounding completion gate | HIGH | `spec.md`, `contracts/*`, `data-model.md` | The previous artifacts did not make exact current file discovery a completion condition. | Added FR-024, SC-010, path fields/validation to data model, and path-grounding requirements to stage/boundary/completion contracts. |
| A04 | Backend query/RPC preservation too implicit | MEDIUM | `tasks.md`, `quickstart.md` | Public contracts were protected generally, but tasks did not explicitly capture query/RPC contract snapshots before refactor. | Expanded T022 to include backend query/RPC contract snapshots alongside representative analysis output. |
| A05 | Existing checklist stale after tasks generation | LOW | `checklists/requirements.md` | Readiness text still referred to plan/task derivation rather than implementation readiness. | Updated readiness wording and appended an implementation handoff addendum. |
| A06 | Checklist IDs absent for the new review | LOW | `checklists/requirements.md` | Existing checklist was readable but not globally ID-addressable for the new handoff review. | Created `checklists/implementation-handoff.md` with CHK001-CHK020. |

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 boundary | Yes | T017-T021, T041, T057, T069, T086, T096, T108 | Inventory and docs force boundary classification. |
| FR-002 typed outcomes | Yes | T010-T016, T027-T040, T058-T067, T070-T077, T087-T094 | Covered for Python, frontend, and VS Code. |
| FR-003 established libraries | Yes | T001-T003, T007-T008, T097 | Uses existing Python `Expression` and TypeScript `Effect`; removes conflicting helpers. |
| FR-004 Python stages | Yes | T010-T013, T028-T057, T058-T067 | Backend core/enrichment/history. |
| FR-005 TypeScript stages | Yes | T014-T015, T070-T086, T087-T096 | Frontend and bridge. |
| FR-006 function adapters | Yes | T012, T030, T038-T040, T062-T067, T074, T090-T094 | Effect/framework shells wrapped. |
| FR-007 compatibility | Yes | T022, T026, T058, T070-T072, T087, T105-T107 | Includes query/RPC snapshots after hardening. |
| FR-008 Python backend axis | Yes | T025-T069 | Core, enrichment, history/effects. |
| FR-009 TS read/UI axis | Yes | T070-T086 | API/RPC, mapping, transforms, render shells. |
| FR-010 object shells | Yes | T048-T049, T082-T085, T087-T096, T103, T108 | AST/React/VS Code shells stay at boundaries. |
| FR-011 error context | Yes | T011, T014-T016, T040, T067, T077, T091-T094 | Typed error context and mapping. |
| FR-012 recoverable vs orchestration | Yes | T042-T057, T058-T069 | Domain failures vs orchestration failures. |
| FR-013 vocabulary | Yes | T010, T017-T021, T101-T103 | Stage names in docs and inventory. |
| FR-014 tests | Yes | T022-T027, T042-T043, T058-T059, T070-T072, T087, T100, T105-T107 | Success/failure/adapter/architecture tests. |
| FR-015 docs | Yes | T009, T020-T021, T068, T101-T104, T110 | Stage, adapter, migration docs. |
| FR-016 no hidden globals | Yes | T017-T021, T028-T057, T100, T109 | Enforced through stage contracts and anti-cosmetic checks. |
| FR-017 immutable boundaries | Yes | T020, T028-T057, T079-T083 | Stage contracts and view-model transforms. |
| FR-018 old helpers | Yes | T097-T099 | Cleanup tasks. |
| FR-019 anti-cosmetic | Yes | T009, T020, T025, T037-T041, T100, T109 | Explicit. |
| FR-020 shell classification | Yes | T017-T021, T041, T057, T069, T086, T096, T108 | Inventory required. |
| FR-021 adapter removal plan | Yes | T021, T038, T056, T098-T099, T108 | Cleanup path. |
| FR-022 frontend derivation out of UI | Yes | T079-T085 | Path-corrected to transforms/pages/components. |
| FR-023 observable typed propagation | Yes | T027, T042-T043, T058-T059, T070-T077, T087-T094 | Short-circuit and recoverable cases. |
| FR-024 path grounding | Yes | T017-T019, T021, T025, T039, T066, T082-T085, T096 | Added during hardening. |

## Constitution Alignment Issues

No constitution conflicts remain. `.specify/memory/constitution.md` is present and applicable; Python ROP vocabulary now follows its `Expression` Result/Option requirement.

## Unmapped Tasks

No task is intentionally unmapped after hardening. Setup, Spec Kit handoff docs, validation, cleanup, and inventory tasks map to FR-001, FR-003, FR-007, FR-014, FR-015, FR-018, FR-019, FR-020, FR-021, and FR-024.

## Metrics

- Total Requirements: 24 functional requirements + 10 success criteria
- Total Tasks: 110
- Coverage %: 100% by requirement-to-task mapping
- Ambiguity Count: 0 open `[NEEDS CLARIFICATION]`; 3 high-risk ambiguities remediated
- Duplication Count: 0 material duplicates after task reordering
- Critical Issues Count: 1 found, 1 remediated

## Next Actions

Proceed to implementation only after T017-T019 inventory records exact current entrypoint files in the target repository checkout. Do not begin code movement from pipeline names alone.
