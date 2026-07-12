# Requirements Traceability: 011 Contract Runtime Codegen

This file is authoritative for implementation scope. Task ranges are inclusive. A task MUST NOT introduce behavior outside the mapped requirements.

| Requirement range | Task IDs | Decision |
|---|---|---|
| FR-001–FR-010 | T007–T029, T046–T061 | Separate REST/non-REST ownership; validate namespaces and output paths. |
| FR-011–FR-020 | T023–T029, T035–T041, T062–T101 | Deterministic headers, sorting, rendering, and no business logic. |
| FR-021–FR-030 | T020–T032, T057–T058, T112–T122 | Exact root commands and thin CLI wrappers. |
| FR-031–FR-036 | T033–T034, T123–T126 | Static API freshness; API diff remains report-only. |
| FR-037–FR-051 | T127–T151 | Runtime conformance uses `/api/v1/status` only and the fixed fixture repository. |
| FR-052–FR-059 | T046–T051, T062–T074 | Single error catalog and generated Python/frontend/VS Code/docs artifacts. |
| FR-060–FR-067 | T055–T056, T075–T088 | Python progress union is authoritative; Ajv validates TypeScript consumers. |
| FR-068–FR-072 | T171–T180 | Scope fixed to progress, worker IPC envelopes, and legacy RPC compatibility. |
| FR-073–FR-078 | T052–T054, T089–T101 | JSON Schema is the sole webview protocol source. |
| FR-079–FR-087 | T152–T180 | Python `src/ppi/worker_ipc/` models are sole worker source; `contracts/rpc-methods.yaml` is sole legacy RPC source. |
| FR-088–FR-094 | T035–T038, T102–T111, T181–T184 | Generated docs/index/fixtures are committed and deterministic. |
| FR-095–FR-104 | T185–T190 | `make mypy-p0` is the only blocking typing gate in spec 011. |
| FR-105–FR-111 | T191–T193 | Import Linter is report-only and uploaded as a CI artifact. |
| FR-112–FR-117 | T123–T151, T191–T216 | Separate static, non-REST, runtime, typing, and architecture jobs with exact blocking policies. |
| P2 plugin manifest scope | T194–T201 | Plugin schema/types/docs only; no loader and no typed i18n. |
