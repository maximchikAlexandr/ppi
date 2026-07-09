# Constitution Alignment and Coverage Gap Checklist: Frontend Platform and Public API Contract Foundation

**Feature**: `010-frontend-api-platform`  
**Created**: 2026-07-08  
**Focus**: constitution alignment, stale-artifact, and diagnostics-coverage gaps found on re-analysis  
**Audience**: specification authors, planners, reviewers

## Constitution Alignment (Requirements Quality)

- [ ] CHK001 Does the plan require an explicit constitution alignment check against `.specify/memory/constitution.md`? [Gap, Plan §12]
- [ ] CHK002 Is the plan's claim "No `memory/constitution.md` exists" accurate, and if not, is the Constitution Check section rewritten? [Consistency, Plan §12]
- [ ] CHK003 Are constitution Principle IV (generic UI over registry) and Principle II (core independence) explicitly mapped to spec FRs? [Traceability, Constitution §II/§IV]
- [ ] CHK004 Is there a requirement that `v1_schemas.py` placement respects Principle VI ("Pydantic ONLY at the FastAPI boundary")? [Ambiguity, Constitution §VI, Plan §4]
- [ ] CHK005 Does the spec or plan require backend projections to remain core-independent (no transport/HTTP dependency) per Principle II? [Coverage, Constitution §II]
- [ ] CHK006 Is the boundary between core (msgspec) and FastAPI (Pydantic) explicitly documented in plan §4 for the v1 schema/projection split? [Clarity, Constitution §VI]

## Stale Artifact (Requirements Quality)

- [ ] CHK007 Is the analysis-report finding A001 ("Missing Artifact constitution.md") still accurate given the constitution exists? [Consistency, Analysis-report A001]
- [ ] CHK008 Is task T155 ("Add workspace-local constitution note") still needed, or should it be rewritten to link the existing constitution? [Consistency, Tasks T155]
- [ ] CHK009 Is the analysis-report metric "Total Tasks: 154" updated to reflect T155-T180 (180 tasks)? [Measurability, Analysis-report]
- [ ] CHK010 Is the coverage summary in `analysis-report.md` extended to FR-110..FR-113? [Traceability, Analysis-report]

## Diagnostics Coverage (Requirements Quality)

- [ ] CHK011 Are requirements defined for a test that default user-facing projections exclude diagnostics-only data? [Gap, Spec §FR-111, §SC-018]
- [ ] CHK012 Is there a requirement that evidence and parse errors are provably absent from default graph/table/dashboard projections? [Coverage, Spec §FR-112]
- [ ] CHK013 Is the distinction between canonical analysis records and UI projections (FR-110) measurable through a dedicated test? [Measurability, Spec §FR-110]
- [ ] CHK014 Does the plan define when the diagnostics capability is required to surface diagnostics-only data in a projection? [Clarity, Spec §FR-111]

## Naming and Governance (Requirements Quality)

- [ ] CHK015 Is "deprecation policy" (FR-094) defined distinctly from "breaking-change detection" in the task documentation? [Clarity, Spec §FR-094, Tasks T144]
- [ ] CHK016 Are Spectral rules required to enforce consistent request parameter naming across `/api/v1` endpoints (not just property casing)? [Coverage, Spec §FR-071, Tasks T006]
- [ ] CHK017 Is `commitOrder` uniqueness/monotonicity specified to resolve greatest-commitOrder tie-breaking under rebase/cherry-pick scenarios? [Ambiguity, Data-model §17.6]
- [ ] CHK018 Are the three stability-gate FRs (FR-090/FR-091/FR-092) consolidated under a single normative pointer to avoid redundancy drift? [Consistency, Spec §FR-090..FR-092]

## Checklist Result

Re-analysis on 2026-07-08 found 2 CRITICAL constitution-alignment issues (plan §12 false claim, no explicit mapping) and a MEDIUM diagnostics-exclusion coverage gap (FR-111/FR-112/SC-018 lack a dedicated test task). Resolve CHK001-CHK006 before `/speckit-implement`; CHK011-CHK014 before Phase 2 exit criteria.