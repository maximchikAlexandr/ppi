# Requirements Quality Checklist: Implementation Handoff Hardening

**Spec**: `specs/008-rop-pipeline-migration/spec.md`  
**Date**: 2026-07-04  
**Focus**: Make the artifacts safe for a less capable code-generation model by removing ambiguous paths, phase-order contradictions, and cosmetic-migration loopholes.

## Path Grounding

- [x] CHK001 Are backend target paths defined against the current repository layout rather than inferred from feature names? [Spec §Repository Path Guardrails] [Gap]
- [x] CHK002 Are frontend target paths defined against `frontend/src/api`, `frontend/src/transforms`, `frontend/src/pages`, and `frontend/src/components` instead of invented folders? [Spec §Repository Path Guardrails] [Gap]
- [x] CHK003 Are exact current entrypoint files required in the migration inventory before existing code is edited? [Contracts §Migration Inventory Template] [Clarity]
- [x] CHK004 Are directory-scoped tasks required to record exact file paths before changing code? [Tasks §Format Validation] [Clarity]
- [x] CHK005 Are newly created paths distinguishable from existing paths that must already be present? [Spec §FR-024] [Completeness]

## Cross-Artifact Consistency

- [x] CHK006 Are task phases ordered consistently with the plan's intended migration sequence? [Plan §Milestones] [Consistency]
- [x] CHK007 Are task IDs and dependency references aligned after reordering history before frontend/VS Code work? [Tasks §Dependencies] [Consistency]
- [x] CHK008 Are spec success criteria reflected by concrete tasks, including path-grounding success criteria? [Spec §SC-010] [Coverage]
- [x] CHK009 Are data-model entities updated so path grounding is part of stage and inventory quality? [Data Model §PipelineStage] [Completeness]
- [x] CHK010 Are contracts updated so a pipeline cannot be marked complete while target paths or old entrypoints are unknown? [Contracts §Completion Contract] [Measurability]

## Anti-Cosmetic Migration Quality

- [x] CHK011 Is a covered process explicitly rejected when it only wraps unchanged imperative internals in `pipe` or `flow`? [Spec §Anti-Cosmetic Acceptance Rule] [Clarity]
- [x] CHK012 Are compatibility adapters prevented from counting as migrated pipelines? [Data Model §CompatibilityAdapter] [Measurability]
- [x] CHK013 Are remaining imperative/object shells required to have adapter names, target paths, and justifications? [Data Model §EffectShell] [Completeness]
- [x] CHK014 Are recoverable domain failures and unrecoverable orchestration failures distinguished in requirements and tasks? [Spec §FR-012] [Consistency]
- [x] CHK015 Are success/failure/adapter tests required for each migrated major pipeline family? [Spec §FR-014] [Coverage]

## Implementation Safety

- [x] CHK016 Are public contracts protected for CLI, JSON-RPC, persisted history, progress events, dashboard, and VS Code commands? [Spec §FR-007] [Coverage]
- [x] CHK017 Are backend query/RPC contract snapshots included before refactors can affect read surfaces? [Tasks §T022] [Coverage]
- [x] CHK018 Are frontend schema/decode/mapping errors required to be distinguishable before UI rendering changes? [Tasks §T070-T077] [Measurability]
- [x] CHK019 Are VS Code lifecycle and cancellation requirements kept as boundary behavior rather than forced pure code? [Tasks §T087-T096] [Clarity]
- [x] CHK020 Are cleanup tasks sufficient to remove deprecated pipe helpers, compatibility wrappers, and unreviewed shells before completion? [Tasks §T097-T110] [Completeness]

## Library and Documentation Source of Truth

- [x] CHK021 Is Python ROP vocabulary fixed to existing `Expression` instead of allowing `returns` or another second Result/Option model? [Spec §Assumptions, Plan §Library Direction, Research §Decision 1] [Clarity]
- [x] CHK022 Is TypeScript ROP vocabulary fixed to `Effect` for async/effect flows without leaving `fp-ts`/`neverthrow` as implementation-time choices? [Plan §Library Direction, Research §Decision 2] [Clarity]
- [x] CHK023 Are all implementation inventory and stage-contract documentation targets kept inside `specs/008-rop-pipeline-migration/` instead of creating a parallel `docs/architecture` source of truth? [Tasks §T017-T021, §T101-T110] [Consistency]
- [x] CHK024 Does the plan's Constitution Check reference the actual `.specify/memory/constitution.md` and account for its `Expression` requirement? [Plan §Constitution Check] [Consistency]
