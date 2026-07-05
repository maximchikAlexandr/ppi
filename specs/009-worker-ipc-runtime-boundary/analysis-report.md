# Specification Analysis Report: Worker IPC Runtime Boundary

**Date**: 2026-07-05  
**Scope**: `spec.md`, `plan.md`, `tasks.md`, contracts, data model, quickstart, and available repository facts.  
**Audience**: implementation by a weaker model that needs explicit, non-ambiguous instructions.

## Findings

| ID | Category | Severity | Location(s) | Summary | Remediation Applied |
|----|----------|----------|-------------|---------|---------------------|
| ANL001 | Ambiguity | HIGH | `spec.md` §4.3, §6.2; `plan.md` §6; `tasks.md` T084 | The spec prohibited a `ready` state while also requiring `worker.ready`, which could lead an implementer to add `ready` to `WorkerState`. | Clarified that `worker.ready` is an event type only and its payload `state` is exactly `idle`; added tests to enforce no `ready` state. |
| ANL002 | Conflict | HIGH | `plan.md` §13; `contracts/protocol.md` §7.6; `quickstart.md` §7; `tasks.md` T104-T105 | Query names listed in the spec did not match the current repository `QueryMethod` enum. The reviewed archive used future/legacy names such as `catalog` and `snapshot/modules`, and incorrectly treated current names such as `project/info` as unsupported. | Replaced whitelist with current `QueryMethod` values from code and added contract coverage task T129. |
| ANL003 | Ambiguity | HIGH | `spec.md` §5.2 `query.execute`; `plan.md` §13; `contracts/protocol.md` §7.6; `tasks.md` T099-T100 | Query result normalization was underspecified for dict, list, scalar, Pydantic, and limit/truncation behavior. | Added deterministic normalization rules and tests for dict/list/scalar/Pydantic/limit cases. |
| ANL004 | Ambiguity | MEDIUM | `contracts/cli.md`; `tasks.md` T089 | CLI progress display allowed "events or polling" without priority/fallback semantics. | Set event subscription as first choice and `analysis.status` polling as fallback after subscription failure/disconnect. |
| ANL005 | Consistency | MEDIUM | `spec.md` §5.2 | Duplicate `Rules:` header in `worker.shutdown` could confuse parser-like agents. | Removed duplicate heading. |
| ANL006 | Coverage | MEDIUM | `.specify/memory/constitution.md`; `plan.md` §17 | The reviewed archive checked the wrong constitution path and claimed no constitution existed. The real constitution existed and had a stale SQLite-specific registry wording that conflicted with the 009 JSON registry contract. | Updated `plan.md` §17 and clarified the constitution to require a global local registry role without forcing SQLite. |

## Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| FR-001 to FR-006 Worker ownership and client boundary | Yes | T039-T057, T106-T119, T120-T121 | Covered by runtime, CLI, FastAPI, IDE contract, and architecture guardrails. |
| FR-007 to FR-011 Registry/runtime metadata and diagnostics | Yes | T018-T027, T058-T073 | Covered by runtime paths, registry, metadata, locks, stale diagnostics. |
| FR-012 to FR-021 Commands and invalid command behavior | Yes | T031-T038, T039-T041, T080-T083, T095-T105, T122 | Covered; query whitelist now synchronized with repository enum. |
| FR-022 to FR-025 Events | Yes | T034-T036, T083-T086, T123 | Covered; `worker.ready` clarified as event-only. |
| FR-026 to FR-030 Errors/protocol compatibility | Yes | T007-T011, T037-T038, T124 | Covered by protocol/error contract tests. |
| FR-031 to FR-037 Lifecycle | Yes | T044-T073, T091-T093 | Covered by supervisor/gateway/integration tasks. |
| FR-038 to FR-042 Security/boundaries | Yes | T016-T019, T106-T121 | Covered by Unix endpoint scope, architecture guardrails, and explicit exclusions. |
| FR-043 to FR-045 Migration | Yes | T006, T087-T090, T102-T104, T111, T119 | Covered; legacy CLI language tightened from MAY to MUST for this feature. |
| NFR-001 to NFR-005 | Yes | T003, T046-T049, T077, T079, T128 | Covered by constants, gateway timeouts, progress, and validation tasks. |

## Constitution Alignment Issues

`.specify/memory/constitution.md` exists and was reviewed on 2026-07-05. The feature is aligned with the constitution after clarifying the constitution's registry wording from a SQLite-specific registry to a storage-neutral global local registry role. The concrete 009 MVP remains JSON at `~/.local/share/ppi/workspaces.json` and explicitly forbids SQLite for this feature.

## Unmapped Tasks

No clearly unmapped implementation tasks remain. Documentation tasks T116-T119 are intentionally non-blocking for Python IPC MVP but required before merge.

## Metrics

- Total Requirements: 45 functional + 5 non-functional
- Total Tasks: 129 listed task IDs after adding T129
- Coverage %: 100% for listed functional/non-functional requirements at task level
- Ambiguity Count: 5 material ambiguities/conflicts found and remediated
- Duplication Count: 1 duplicate heading found and remediated
- Critical Issues Count: 0
- High Issues Count: 3 remediated

## Next Actions

Implement tasks in order. Do not start coding from the old archive; use this reviewed archive because it contains the corrected query whitelist and explicit `worker.ready` semantics.
