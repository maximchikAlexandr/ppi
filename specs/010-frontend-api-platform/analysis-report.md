# Specification Analysis Report

| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|
| A001 | Constitution Alignment | CRITICAL | `plan.md` §12; `.specify/memory/constitution.md` | Plan §12 previously claimed no constitution exists and skipped the constitution check. Constitution v1.1.1 exists at `.specify/memory/constitution.md`. | Rewrote plan §12 with explicit alignment table mapping Principles II/IV/VI to FRs and `v1_schemas.py` placement. |
| A101 | Hardening | HIGH | T155-T178 (Phase 12) | Implementation may diverge on the seven ambiguity gaps identified after task generation. | Added explicit cross-reference to constitution v1.1.1, latest-commit default test, store-not-ready error tests, public-camelCase property tests, fallback-label unit tests, generic value renderer tests, adapter contract tests, boundary scanner import + violation-output tests, `MetricQueryStateResult` no-request rule, dashboard no-request tests, non-blocking missing-baseline message, baseline promotion instructions, HTTP status mapping tests, projection-boundary + diagnostics-exclusion tests, canonical-vs-projection tests, `projections.py` named-only marker, camelCase alias serialization test, `publicApi` facade test, and `legacy/README.md` policy. |
| A102 | Implementation | MEDIUM | `tasks.md` §Phase 12 | Some Phase 12 items overlap with earlier phases. | Mapped each Phase 12 item to the file or test it produces and verified all artifacts exist. |
| A002 | Consistency | HIGH | `.speckit-chat/decision-log.md`; `spec.md` FR-073 | Decision log still said `/api/v1` default field naming was `snake_case`, contradicting later clarification Q5 and FR-073. | Marked the old decision as superseded and made `camelCase` normative. |
| A003 | Ambiguity | HIGH | `contracts/api-contract.md`; `data-model.md`; `spec.md` Edge Cases | Latest commit selection was implied but not deterministic. | Added greatest-`commitOrder` default for omitted `commitId`. |
| A004 | Ambiguity | HIGH | `contracts/api-contract.md`; `spec.md` FR-070 | Error handling named a common shape but did not map common store/query failures to it. | Added minimum status-code and `STORE_NOT_READY` behavior. |
| A005 | Terminology Drift | MEDIUM | `contracts/frontend-platform-contract.md`; `tasks.md` T114 | Dashboard helper was named `getValidAggregations` in one artifact and `getValidAggregationsForMetric` in another. | Standardized on `getValidAggregationsForMetric`. |
| A006 | Ambiguity | MEDIUM | `data-model.md` TableRowAction; `api-contract.md` table endpoint | Drilldown action parameter flow was underspecified and could cause agents to reintroduce `module_name`. | Added explicit row-action parameter rules and made `GET /api/v1/tables/{tableId}` the only initial generic drilldown route. |
| A007 | Coverage Gap | MEDIUM | `frontend-platform-contract.md`; `migration-boundaries.md` | Boundary scanner requirements were listed at a high level but not executable enough. | Added deterministic scanner requirements including import checks, token checks, exit codes, and violation output. |
| A008 | Ambiguity | MEDIUM | `spec.md`; `data-model.md` | Unknown id/value fallback behavior was required but not algorithmically defined. | Added deterministic fallback label and value-rendering rules. |
| A009 | Coverage Gap | MEDIUM | `contracts/governance-contract.md` | Missing OpenAPI baseline handling before stable promotion could be implemented inconsistently. | Added exact missing-baseline behavior and baseline promotion rules. |
| A010 | Task Coverage | LOW | `tasks.md` | Task order had many parallel markers that may be unsafe for weak agents. | Added a conservative weak-agent execution order in `plan.md`. |
| A011 | Constitution Alignment | CRITICAL | `plan.md` §4; `.specify/memory/constitution.md` Principle VI | `v1_schemas.py` (Pydantic) was placed in `src/ppi/query/`, violating Principle VI ("Pydantic ONLY at the FastAPI boundary"). | Moved `v1_schemas.py` to `src/ppi/server/`; `projections.py` returns plain structures. |
| A012 | Coverage Gap | MEDIUM | `spec.md` FR-111, FR-112, SC-018; `tasks.md` | No dedicated test task verifies that default user-facing projections exclude diagnostics-only data (evidence, parse errors). | Added test task for diagnostics exclusion in Phase 2. |
| A013 | Ambiguity | MEDIUM | `spec.md` FR-094; `tasks.md` T144 | "Deprecation policy" (FR-094) conflated with "breaking-change detection" in task documentation. | Clarified T144 to require explicit deprecation timeline/sunset/migration path distinct from breaking-change detection. |

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001..FR-011 | Yes | T026-T045 | Generic primitives, registry, provider, fallback rendering. |
| FR-012..FR-022 | Yes | T033-T037, T046-T054 | UI config definitions and backend projection coverage. |
| FR-023..FR-029 | Yes | T027, T038-T045, T112-T124 | Metric definitions, renderers, and dashboard query validation. |
| FR-030..FR-042 | Yes | T083-T097 | Generic graph migration. |
| FR-043..FR-053 | Yes | T098-T111 | Generic table and drilldown migration. |
| FR-054..FR-062 | Yes | T112-T124 | Dashboard state normalization and valid-request prevention. |
| FR-063..FR-079 | Yes | T011-T025, T046-T070, T071-T082 | `/api/v1`, schemas, generated transport, facade, adapters. |
| FR-080..FR-093 | Yes | T001-T010, T136-T150 | Export, lint, bundle, generation, diff, baseline documentation. |
| FR-094 | Yes | T144 | Deprecation policy; clarified as distinct from breaking-change detection (A013). |
| FR-095..FR-104 | Yes | T125-T135, T151 | Legacy adapters and boundary enforcement. |
| FR-105..FR-109 | Yes | T016-T017, T071-T077 | Backend projection responsibility; clarified by HD-005. |
| FR-110 | Partial | T016-T017, T062-T065 | Projection layer distinguishes canonical records from projections. |
| FR-111..FR-112 | Yes | T062-T065, new diagnostics-exclusion test | Now covered after A012 remediation. |
| FR-113 | N/A | — | MAY permission; no task needed. |

## Constitution Alignment Issues

Resolved. Plan §12 now performs explicit alignment against `.specify/memory/constitution.md` v1.1.1:
- Principle II (core independence): `v1_schemas.py` moved to `src/ppi/server/` (A011).
- Principle IV (generic UI over registry): mapped to FR-001..FR-011.
- Principle VI (Pydantic only at FastAPI boundary): `v1_schemas.py` placed at boundary; `projections.py` returns plain structures.

## Unmapped Tasks

No clearly unmapped tasks found. Polish tasks T145-T154 are cross-cutting validation tasks and intentionally map to multiple requirements.

## Metrics

- Total Requirements: 113 functional requirements (FR-001..FR-113) plus 10 hardening defaults
- Total Success Criteria: 21 (SC-001..SC-021)
- Total Tasks: 180 (T001..T180) after hardening tasks T155-T180
- Coverage %: approximately 98% after A012 diagnostics-exclusion task addition
- Ambiguity Count: 9 material ambiguities found across analysis runs (A002..A013)
- Duplication Count: 0 duplicate functional requirements found
- Critical Issues Count: 2 constitution-alignment issues (A001, A011) — both resolved

## Next Actions

1. Assign implementation only after the implementation-readiness checklist is reviewed.
2. `/api/v1` remains experimental until Graph, Tables, and Metrics Dashboard reach `generic_component` state and validation passes.
3. Run `/speckit-analyze` again after implementation to confirm residual issues are closed.