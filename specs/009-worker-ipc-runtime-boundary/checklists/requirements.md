# Requirements Quality Checklist: Worker IPC Runtime Boundary

**Feature**: `009-worker-ipc-runtime-boundary`  
**Updated**: 2026-07-04  
**Purpose**: Validate that the IPC feature specification is explicit enough for implementation by a less capable model without requiring product-behavior guessing.

## Scope Quality

- [x] Feature goal is clearly stated.
- [x] In-scope work is explicit.
- [x] Out-of-scope work is explicit.
- [x] Public webserver to local-worker reverse connectivity is excluded.
- [x] Remote Git repository import is excluded.
- [x] Full plugin refactor is excluded.
- [x] Direct browser-to-worker communication is excluded.

## User Behavior Coverage

- [x] Web UI behavior is specified.
- [x] IDE behavior is specified.
- [x] CLI behavior is specified.
- [x] Multi-client behavior is specified.
- [x] Stale runtime recovery behavior is specified.
- [x] Duplicate startup behavior is specified.
- [x] Protocol mismatch behavior is specified.
- [x] Running-analysis duplicate request behavior is specified.

## Data and State Completeness

- [x] Workspace registration fields are listed.
- [x] Runtime metadata fields are listed.
- [x] Worker lifecycle states are listed.
- [x] Analysis status states are listed.
- [x] Command envelope fields are listed.
- [x] Response envelope fields are listed.
- [x] Event envelope fields are listed.
- [x] Error object fields are listed.

## Command Completeness

- [x] `worker.health` is specified.
- [x] `workspace.info` is specified.
- [x] `analysis.status` is specified.
- [x] `analysis.start` is specified.
- [x] `analysis.cancel` is specified.
- [x] `query.execute` is specified.
- [x] `events.subscribe` is specified.
- [x] `worker.shutdown` is specified.
- [x] Required command payload/result fields are specified.
- [x] Unsupported command behavior is specified.
- [x] Invalid request behavior is specified.

## Event and Error Completeness

- [x] Required event types are listed.
- [x] Required event payload fields are listed.
- [x] Required error codes are listed.
- [x] Recoverability defaults are listed for errors.
- [x] Tracebacks are not accepted as primary client responses.

## Testability

- [x] Acceptance tests are written in Given/When/Then style.
- [x] Functional requirements have stable IDs.
- [x] Success criteria are measurable.
- [x] Edge cases are explicit.
- [x] Implementation can be tested without real IDE/browser dependencies.

## Ambiguity Review

- [x] No `[NEEDS CLARIFICATION]` markers remain.
- [x] Assumptions are documented.
- [x] Explicit implementer decisions are documented.
- [x] Terms are defined in key entities.
- [x] No requirement depends on unspecified cloud/auth/public networking behavior.

## Readiness

- [x] Ready for `speckit-tasks` and implementation.
- [x] Planning phase has fixed module layout, transport/framing, process supervisor behavior, test fixtures, and migration sequence.

## Implementation Explicitness Addendum

- [x] Feature is numbered as `009-worker-ipc-runtime-boundary`.
- [x] Module layout is fixed to `src/ppi/worker_ipc/`.
- [x] CLI command names are fixed for the existing global `--repo` CLI shape.
- [x] Runtime paths are fixed.
- [x] Duplicate `analysis.start` behavior is fixed to successful `already_running`.
- [x] Query while analysis is running is fixed to `WORKER_BUSY`.
- [x] `worker.shutdown` while analysis is running is fixed to `WORKER_BUSY`.
- [x] TCP/WSS/public-webserver-to-local-worker work is excluded.
