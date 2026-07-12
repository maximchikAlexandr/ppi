# Specification Analysis Report — 011 Contract Runtime Codegen

## Findings and Applied Resolutions

| ID | Category | Severity | Location(s) | Finding | Applied resolution |
|---|---|---:|---|---|---|
| A001 | Missing governance input | HIGH | workspace | `memory/constitution.md` is absent, so constitution alignment cannot be proven. | Recorded as the only residual risk; all internal MUST rules were cross-checked. |
| A002 | Ambiguous source ownership | CRITICAL | worker IPC contracts | Worker IPC allowed Python models or fallback JSON Schema. | Selected existing `src/ppi/worker_ipc/` msgspec models as the sole source; schema export failure is fatal. |
| A003 | Optional compatibility scope | HIGH | RPC/CLI contract, plan, tasks | Legacy RPC generation depended on whether a consumer “still needs” it. | Made compatibility catalog mandatory because `ppi rpc` is documented as supported; source fixed to `contracts/rpc-methods.yaml`. |
| A004 | Undefined readiness fallback | HIGH | API runtime contract, plan | Legacy `/api/status` fallback was optional. | Removed fallback; `/api/v1/status` is the sole readiness endpoint. |
| A005 | Indeterminate CI blocking | CRITICAL | FR-036, FR-103, FR-110–111 | API diff, mypy, and Import Linter could change between blocking/non-blocking states. | Fixed policy: API diff report-only; `mypy-p0` blocking; whole-project mypy absent; Import Linter report-only for all spec 011. |
| A006 | Open-ended JSON scope | HIGH | FR-069 | CLI JSON contracts could expand later without a fixed list. | Fixed scope to progress, worker IPC envelopes, and legacy RPC compatibility. |
| A007 | Optional P2 work | MEDIUM | plan/tasks | Typed i18n could be implemented “if beneficial.” | Excluded typed i18n from spec 011. Plugin manifest schema/types/docs remain mandatory P2 scope. |
| A008 | Numbering/coverage drift | HIGH | spec stories and sections | User Story 7 and section K were missing; tasks used US7/US8 differently. | Renumbered stories and added FR-079–FR-087 for worker IPC/RPC compatibility. |
| A009 | Entity mismatch | MEDIUM | data-model vs spec | `storage` was a valid owner in spec but absent from `ContractSource.owner`. | Added `storage` to the data model owner union. |
| A010 | Conditional VS Code artifacts | MEDIUM | plan/contracts | Outputs were conditional even though repository contains `vscode-extension/`. | Made VS Code generated artifacts and facades required. |
| A011 | Weak traceability | HIGH | tasks.md | 216 tasks had story tags but no authoritative FR mapping. | Added `requirements-traceability.md` and a mandatory task traceability rule. |

## Coverage Summary

All FR ranges FR-001–FR-117 now map to explicit task ranges in `requirements-traceability.md`. P2 plugin work is also mapped. No intentionally unmapped implementation tasks remain.

## Constitution Alignment Issues

The archive does not contain `memory/constitution.md`; therefore no claim of full constitution compliance is made. This is a missing-input risk, not an unresolved product decision.

## Metrics

- Total functional requirements: 117
- Total implementation tasks: 216
- Requirement coverage after remediation: 100% by authoritative range mapping
- Ambiguities resolved: 10
- Duplicate/conflicting policy groups resolved: 4
- Remaining critical issues: 0 within supplied artifacts
- Remaining external risk: missing constitution file
