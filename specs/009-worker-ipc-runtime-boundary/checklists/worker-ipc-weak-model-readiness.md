# Requirements Quality Checklist: Worker IPC Weak-Model Readiness

**Feature**: `009-worker-ipc-runtime-boundary`  
**Created**: 2026-07-05  
**Focus**: ambiguity and implementability review for a weaker implementation model.

- [x] CHK001 Are lifecycle states fully enumerated without hidden aliases such as `ready`? [Clarity] [Spec §4.3]
- [x] CHK002 Is `worker.ready` clearly classified as an event type rather than a worker state? [Ambiguity] [Spec §6.2]
- [x] CHK003 Are command payload and result fields defined for every required command? [Completeness] [Spec §5.2]
- [x] CHK004 Are duplicate analysis-start semantics objective and non-erroring? [Clarity] [Spec §5.2 analysis.start]
- [x] CHK005 Is busy query behavior defined with a single required error code? [Consistency] [Spec §5.2 query.execute]
- [x] CHK006 Are allowed query names synchronized with repository `QueryMethod` values? [Consistency] [Plan §13] [Contract §7.6]
- [x] CHK007 Are deprecated/nonexistent query names explicitly rejected? [Coverage] [Contract §7.6]
- [x] CHK008 Is query result normalization deterministic for dict/list/scalar/Pydantic outputs? [Clarity] [Spec §5.2 query.execute]
- [x] CHK009 Is worker-level query `limit` behavior objectively defined? [Measurability] [Contract §7.6]
- [x] CHK010 Are startup lock, health re-check, and duplicate-worker prevention ordered explicitly? [Completeness] [Plan §10]
- [x] CHK011 Are stale metadata decisions based on health checks rather than trusting metadata? [Consistency] [Spec §8.1] [Plan §10]
- [x] CHK012 Are runtime paths exact and testable under both XDG and fallback roots? [Clarity] [Plan §8] [Contract runtime-files]
- [x] CHK013 Are timeout values numeric and centralized in constants? [Measurability] [Plan §5] [NFR-001]
- [x] CHK014 Are transport exclusions explicit enough to prevent TCP/WSS implementation creep? [Coverage] [Spec §10.3] [Tasks rules]
- [x] CHK015 Are CLI command names compatible with the existing global `--repo` shape? [Consistency] [Plan §11]
- [x] CHK016 Are FastAPI responsibilities limited to adapter/proxy behavior? [Boundary] [Plan §15] [Contract adapters]
- [x] CHK017 Are IDE responsibilities limited so the model will not rewrite the extension? [Boundary] [Plan §3] [Contract adapters]
- [x] CHK018 Are legacy direct CLI paths preserved during this feature? [Migration] [Spec §13 FR-043]
- [x] CHK019 Are event replay expectations explicitly excluded? [Scope] [Plan §14]
- [x] CHK020 Are architecture guardrail tests mapped to storage/server boundary requirements? [Traceability] [Tasks T120-T121]
- [x] CHK021 Is each major feature requirement represented by at least one task group? [Coverage] [Analysis report Coverage Summary]
- [x] CHK022 Are implementation tasks dependency-ordered for a weaker model? [Clarity] [Tasks Dependencies]
- [x] CHK023 Are validation commands listed and concrete? [Measurability] [Tasks Final validation commands]
- [x] CHK024 Is constitution alignment evaluated against the real `.specify/memory/constitution.md` file rather than a missing-path assumption? [Gap] [Plan §17]

## 2026-07-05 Context and Contract Recheck

- [x] CHK025 Is the active Spec Kit feature pointer set to the 009 feature directory? [Consistency] [.specify/feature.json]
- [x] CHK026 Does `AGENTS.md` point implementers to the 009 plan rather than the prior 008 plan? [Consistency] [AGENTS.md]
- [x] CHK027 Are query names in plan/protocol/tasks synchronized with the current `ppi.query.dispatch.QueryMethod` values? [Consistency] [Plan §13] [Contract §7.6]
- [x] CHK028 Are CLI query examples using actual `_cli_metric_to_method` aliases rather than invented aliases such as `modules`? [Clarity] [Contract CLI §6] [Quickstart §7]
- [x] CHK029 Is the registry storage decision consistent between the constitution and feature contracts? [Conflict] [Constitution] [Plan §9] [Contract runtime-files]
- [x] CHK030 Are examples of unsupported query names clearly separated from current supported query names? [Clarity] [Contract §7.6] [Tasks T100]
- [x] CHK031 Does the implementation checklist preserve a weaker model's dependency order and exact command names after the context switch? [Traceability] [Tasks Dependencies]
