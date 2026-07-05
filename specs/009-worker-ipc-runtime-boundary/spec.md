# Feature Specification: Worker IPC Runtime Boundary

**Feature Branch**: `009-worker-ipc-runtime-boundary`  
**Created**: 2026-07-04  
**Updated**: 2026-07-05  
**Status**: Ready for tasks  
**Input**: User request: "доработаем IPC для данного проекта" + follow-up: implementation will be done by a weaker model, so the specification must be explicit and avoid uncertainty.

## 1. Feature Overview

PPI must introduce a clear worker IPC/runtime boundary. For every registered workspace, exactly one active worker process owns analysis execution, query execution, progress events, runtime state, and writes to the workspace analysis storage. External interfaces such as CLI, FastAPI/web UI, and VS Code/Cursor must interact with this worker through one shared command/event boundary instead of each interface directly controlling analysis or writing to storage.

This specification is intentionally concrete. It defines the required commands, states, error categories, lifecycle behavior, registry/runtime metadata, and acceptance criteria so that implementation can proceed without guessing product behavior.

The feature is limited to IPC/runtime foundation. It does not implement the full plugin refactor and does not implement remote Git repository import. It also explicitly excludes public-webserver-to-local-worker reverse connectivity.

## 2. Scope

### 2.1 In Scope

- One active writer worker per workspace.
- Multiple clients connected to the same active worker.
- Shared worker boundary used by:
  - CLI commands;
  - FastAPI/web UI adapter;
  - VS Code/Cursor integration.
- Workspace discovery through a registry.
- Worker discovery through runtime metadata.
- Worker lifecycle states.
- Worker command model.
- Worker event model.
- Structured response and structured error model.
- Stale worker/runtime recovery behavior.
- Protocol version compatibility checks.
- Local IPC as the MVP transport.
- Transport abstraction sufficient to add TCP-over-SSH-tunnel later without changing command semantics.
- Migration compatibility so existing CLI behavior can remain available while worker-based behavior is introduced.

### 2.2 Out of Scope

The following items must not be implemented as part of this feature:

- Full migration to plugin architecture.
- Full extraction of all analyzers, metrics, storage backends, or profiles into plugins.
- New business feature for importing or cloning remote Git repositories.
- Public webserver to local-worker reverse connection mode.
- Cloud multi-user deployment.
- Tenant management.
- Public authentication model.
- Direct browser-to-worker communication.
- Generic remote file manager over worker IPC.
- Replacing the existing analytics domain model.
- Rewriting existing analysis algorithms unless required to route them through the worker.

## 3. Required User-Visible Behavior

### 3.1 Web UI behavior

When a user starts `ppi serve`, the webserver must be able to list registered workspaces and show whether each workspace has an available worker. When the user opens a workspace, the webserver must connect to the active worker or start one if no active worker exists. The webserver must route workspace status, analysis start, progress events, and read-only queries through the worker boundary.

The webserver must not write directly to the active workspace analysis storage in the normal worker-based flow.

### 3.2 IDE behavior

When a user opens a project in VS Code/Cursor, the extension must resolve the current workspace, connect to the existing worker if one is active, or start one if no worker exists. If the webserver already started the worker for that workspace, the IDE must attach to that same worker. The IDE must not create a competing writer.

### 3.3 CLI behavior

When a user runs a CLI command that needs active workspace state, the CLI must use the same worker boundary as the webserver and IDE. If a worker is active, the CLI attaches to it. If no worker is active and the command supports starting one, the CLI starts it and then sends the command.

Existing direct CLI flows MUST remain available during migration; every command that adds `--via-worker` MUST use the worker boundary consistently.

### 3.4 Multi-client behavior

The worker must support at least three simultaneous logical clients for the same workspace: one CLI client, one webserver adapter client, and one IDE client. Disconnecting one client must not stop the worker or disconnect other clients.

## 4. Workspace and Runtime Model

### 4.1 Workspace

A workspace is a registered project known to PPI. Each workspace must have a stable identity and enough metadata for clients to find its project path, analysis storage path, selected analysis profile, and active worker runtime information.

Required workspace registration fields:

| Field | Required | Meaning |
|---|---:|---|
| `workspace_id` | yes | Stable unique workspace identifier. |
| `project_path` | yes | Absolute path to the source project. |
| `analysis_path` | yes | Absolute path to the workspace `.ppi` or external analysis directory. |
| `profile` | yes | Selected analysis profile, for example `python` or `odoo`. |
| `display_name` | yes | Human-readable project name. |
| `created_at` | yes | Registration creation timestamp. |
| `updated_at` | yes | Last registration update timestamp. |

### 4.2 Runtime metadata

Runtime metadata describes the current or last known worker for a workspace. Runtime metadata must be recoverable if stale.

Required runtime metadata fields:

| Field | Required | Meaning |
|---|---:|---|
| `workspace_id` | yes | Workspace served by this worker. |
| `worker_id` | yes | Unique id for one worker process lifetime. |
| `pid` | yes | OS process id of the worker, when local. |
| `endpoint` | yes | Connection endpoint for the active worker. |
| `transport` | yes | Transport kind. MVP value: `unix`. Future value: `tcp`. |
| `protocol_version` | yes | Worker protocol major/minor version. |
| `state` | yes | Last known worker lifecycle state. |
| `started_at` | yes | Worker startup timestamp. |
| `updated_at` | yes | Last metadata update timestamp. |
| `last_heartbeat_at` | yes | Last worker heartbeat timestamp. |

### 4.3 Worker lifecycle states

The worker state MUST use this exact MVP state vocabulary:

| State | Meaning |
|---|---|
| `starting` | Process exists but is not ready to accept normal commands. |
| `idle` | Worker is initialized and has no running analysis. This is the only healthy ready/no-work state in MVP. |
| `busy` | Worker is executing analysis or another long-running exclusive operation. |
| `stopping` | Controlled shutdown was requested. |
| `stopped` | Worker stopped normally. |
| `failed` | Worker failed during startup or runtime. |
| `stale` | Metadata exists but no healthy worker can be reached. |

Rules:

- A newly spawned worker starts as `starting`.
- A worker becomes `idle` after initialization succeeds. The MVP MUST NOT emit or persist a separate worker lifecycle state named `ready`. The event type `worker.ready` is allowed and means "the worker just entered `idle` after startup"; its payload `state` MUST be `idle`.
- A worker becomes `busy` while an analysis run is active.
- A worker returns to `idle` after analysis completes, fails, or is cancelled.
- A client-side discovery flow MUST mark metadata as `stale` when the process or endpoint is unreachable after health check.

## 5. Command Model

### 5.1 General command rules

Every worker request must have:

| Field | Required | Meaning |
|---|---:|---|
| `request_id` | yes | Client-generated id used to match responses. |
| `protocol_version` | yes | Client protocol version. |
| `workspace_id` | yes | Target workspace id. |
| `command` | yes | Command name. |
| `payload` | yes | Command-specific payload object. Empty object if not needed. |

Every worker response must have:

| Field | Required | Meaning |
|---|---:|---|
| `request_id` | yes | Same id as request. |
| `ok` | yes | Boolean success indicator. |
| `result` | yes when `ok=true` | Command-specific result object. |
| `error` | yes when `ok=false` | Structured error object. |

The worker must never return an unstructured traceback as the primary response. Internal tracebacks may be logged, but clients receive structured errors.

### 5.2 Required commands

The worker must implement the following command names and behavior.

#### `worker.health`

Purpose: verify that the endpoint is a healthy compatible worker.

Request payload: `{}`

Successful result fields:

| Field | Meaning |
|---|---|
| `worker_id` | Current worker id. |
| `workspace_id` | Workspace served by the worker. |
| `protocol_version` | Worker protocol version. |
| `state` | Current worker state. The value MUST be one of section 4.3 and MUST NOT be `ready`. |
| `started_at` | Worker startup timestamp. |

#### `workspace.info`

Purpose: return workspace metadata known to the worker.

Request payload: `{}`

Successful result fields:

| Field | Meaning |
|---|---|
| `workspace_id` | Workspace id. |
| `project_path` | Project path. |
| `analysis_path` | Analysis data path. |
| `profile` | Current profile. |
| `display_name` | Display name. |

#### `analysis.status`

Purpose: return current analysis status.

Request payload: `{}`

Successful result fields:

| Field | Meaning |
|---|---|
| `state` | One of `not_started`, `running`, `completed`, `failed`, `cancelled`. |
| `current_run_id` | Current run id or null. |
| `last_run_id` | Most recent run id or null. |
| `progress_percent` | Number from 0 to 100 or null if not measurable. |
| `message` | Human-readable status summary. |

#### `analysis.start`

Purpose: request an analysis run for the workspace.

Request payload fields:

| Field | Required | Meaning |
|---|---:|---|
| `mode` | yes | `full` or `incremental`. |
| `reason` | no | Human-readable reason/source, for example `cli`, `web`, `ide`. |

Successful result fields:

| Field | Meaning |
|---|---|
| `run_id` | New or existing analysis run id. |
| `accepted` | True if worker accepted the request. |
| `state` | `running` or `already_running`. |
| `message` | Human-readable summary. |

Rules:

- If no analysis is running, worker starts a new run and returns `state=running`.
- If analysis is already running, worker MUST NOT start a second simultaneous analysis for the same workspace. MVP behavior is mandatory: return `ok=true`, `accepted=true`, `state=already_running`, and the active `run_id`. The MVP MUST NOT return `ANALYSIS_ALREADY_RUNNING` for this normal idempotent case.

#### `analysis.cancel`

Purpose: request cooperative cancellation of active analysis.

Request payload fields:

| Field | Required | Meaning |
|---|---:|---|
| `run_id` | no | Specific run to cancel. If omitted, cancel current run. |
| `reason` | no | Human-readable reason. |

Successful result fields:

| Field | Meaning |
|---|---|
| `accepted` | Whether cancellation request was accepted. |
| `run_id` | Run affected or null. |
| `message` | Human-readable summary. |

Rules:

- Cancellation is cooperative.
- If no run is active, return success with `accepted=false` and a clear message.
- The worker must keep storage consistent even if cancellation is requested.

#### `query.execute`

Purpose: execute a read-only query against analysis results.

Request payload fields:

| Field | Required | Meaning |
|---|---:|---|
| `query_name` | yes | Name of supported query. MVP supported names MUST be exactly the `ppi.query.dispatch.QueryMethod` string values listed in plan section 13 and contracts/protocol.md section 7.6. |
| `parameters` | yes | Query parameter object. Empty object if none. |
| `limit` | no | Optional maximum number of normalized result rows returned by the worker. If omitted, no worker-level truncation is applied. |

Successful result fields:

| Field | Meaning |
|---|---|
| `columns` | Ordered list of result keys when the normalized rows are objects, otherwise empty list. |
| `rows` | Normalized JSON-compatible rows. If the dispatcher returns a dict/object, wrap it as one row. If it returns a list, use that list. If it returns a scalar, wrap it as one row with key `value`. |
| `row_count` | Number of rows returned after worker-level limit/truncation. |
| `truncated` | True only when the optional `limit` caused the worker to omit rows. |

Rules:

- `query.execute` is read-only.
- Unknown query names MUST return `UNKNOWN_QUERY`. The worker MUST call the existing dispatcher rather than maintaining a divergent hard-coded query list; tests MUST fail if the contract list and `QueryMethod` values drift.
- While analysis is running, MVP `query.execute` MUST return `WORKER_BUSY` for every query. Read queries during active analysis are deferred to a later feature to avoid storage concurrency ambiguity.

#### `events.subscribe`

Purpose: subscribe a client to worker events.

Request payload fields:

| Field | Required | Meaning |
|---|---:|---|
| `event_types` | no | Optional list of event types. If absent, subscribe to all supported event types. |

Successful result fields:

| Field | Meaning |
|---|---|
| `subscription_id` | Subscription id. |
| `accepted_event_types` | Event types that will be delivered. |

Rules:

- Subscribing to events must not block normal request/response commands from other clients.
- Events are live notifications. The worker is not required to replay events emitted before subscription.
- After reconnect, clients must call `analysis.status` to recover current state.

#### `worker.shutdown`

Purpose: request controlled shutdown of the local worker.

Request payload fields:

| Field | Required | Meaning |
|---|---:|---|
| `reason` | no | Human-readable reason. |

Successful result fields:

| Field | Meaning |
|---|---|
| `accepted` | Whether shutdown was accepted. |
| `message` | Human-readable summary. |

Rules:

- The command is for local management flows only.
- If analysis is running, MVP `worker.shutdown` MUST reject the request with `WORKER_BUSY`. Graceful shutdown during active analysis is not implemented in this feature.
- Public remote management semantics are out of scope.

## 6. Event Model

### 6.1 Event envelope

Every event must include:

| Field | Required | Meaning |
|---|---:|---|
| `event_id` | yes | Unique event id. |
| `workspace_id` | yes | Workspace id. |
| `worker_id` | yes | Worker id. |
| `event_type` | yes | Event type name. |
| `created_at` | yes | Event timestamp. |
| `payload` | yes | Event-specific payload object. |

### 6.2 Required event types

| Event type | When emitted | Required payload fields |
|---|---|---|
| `worker.ready` | Worker enters `idle` after startup initialization succeeds. This is an event type only, not a worker lifecycle state. | `state` with exact value `idle` |
| `worker.state_changed` | Worker lifecycle state changes. | `previous_state`, `state` |
| `worker.warning` | Non-fatal worker warning occurs. | `message`, `code` |
| `worker.failed` | Worker enters failed state. | `message`, `code` |
| `analysis.started` | Analysis run starts. | `run_id`, `mode` |
| `analysis.progress` | Analysis progress changes. | `run_id`, `progress_percent`, `message` |
| `analysis.warning` | Non-fatal analysis warning occurs. | `run_id`, `message`, `code` |
| `analysis.completed` | Analysis run completes successfully. | `run_id`, `message` |
| `analysis.cancelled` | Analysis run is cancelled. | `run_id`, `message` |
| `analysis.failed` | Analysis run fails. | `run_id`, `message`, `code` |

## 7. Error Model

### 7.1 Error object

Structured error fields:

| Field | Required | Meaning |
|---|---:|---|
| `code` | yes | Stable machine-readable error code. |
| `message` | yes | Human-readable message. |
| `details` | no | Additional structured context. |
| `recoverable` | yes | Whether retry/remediation may work. |

### 7.2 Required error codes

| Code | Meaning | Recoverable default |
|---|---|---:|
| `INVALID_REQUEST` | Request shape or required fields are invalid. | false |
| `UNKNOWN_COMMAND` | Command name is not supported. | false |
| `INCOMPATIBLE_PROTOCOL` | Client and worker protocol versions are incompatible. | false |
| `WORKSPACE_MISMATCH` | Request workspace id does not match worker workspace. | false |
| `WORKER_NOT_READY` | Worker is starting or not ready. | true |
| `WORKER_BUSY` | Worker cannot execute command while busy. | true |
| `ANALYSIS_ALREADY_RUNNING` | Reserved for future compatibility. MVP `analysis.start` does not use this for the normal duplicate-start case; it returns `already_running` success. | true |
| `NO_ACTIVE_ANALYSIS` | Cancellation requested but no analysis is active. | true |
| `UNKNOWN_QUERY` | Query name is not supported. | false |
| `QUERY_FAILED` | Query execution failed. | true |
| `STORAGE_UNAVAILABLE` | Analysis storage cannot be opened or queried. | true |
| `INTERNAL_ERROR` | Unexpected worker failure. | true |

## 8. Worker Discovery and Startup Rules

### 8.1 Discovery algorithm

A client that needs a worker for a workspace must follow this behavior:

1. Resolve workspace id from explicit argument, current directory, IDE workspace folder, or selected web UI workspace.
2. Load workspace registration.
3. Load runtime metadata if present.
4. If runtime metadata is present, call `worker.health` on the endpoint.
5. If health check succeeds and protocol is compatible, attach to that worker.
6. If health check fails because the process/endpoint is gone, mark runtime metadata as `stale` and attempt startup if the client command allows startup.
7. If no runtime metadata exists, attempt startup if the client command allows startup.
8. If startup is not allowed, return a clear user-facing error that no worker is available.

### 8.2 Startup rules

When starting a worker:

- The system must prevent two active workers from becoming writers for the same workspace.
- Startup must create or update runtime metadata.
- Worker must not become `idle` until workspace identity, analysis path, protocol version, and storage boundary are initialized. Do not use a `ready` lifecycle state.
- If startup fails, runtime metadata must be left in a diagnosable `failed` or `stale` state with an error message available to the initiating client.

### 8.3 Duplicate startup race

If two clients attempt to start the same worker simultaneously:

- At most one process may become the active worker.
- The losing starter must attach to the active worker if it becomes available.
- If neither process becomes healthy, the client must report startup failure with a clear diagnostic.

## 9. Storage Boundary Rules

- The active worker is the only normal writer to the workspace analysis storage.
- Clients must not bypass the worker to write active analysis results.
- Read-only direct access MUST remain only as a legacy or explicit diagnostic path during migration and MUST NOT be used by new worker-backed flows.
- Analysis subprocesses, if used internally by the worker, must return results to the worker for centralized storage writes.
- If the worker crashes during a write, the next startup must detect whether storage is usable and report structured status if recovery is needed.

## 10. Transport Requirements

### 10.1 MVP transport

The MVP must support one local IPC transport for same-machine communication. The expected local endpoint is workspace-scoped and discoverable through runtime metadata.

### 10.2 Future transport compatibility

Command names, response shapes, event shapes, and error codes must not depend on the local transport. A future TCP endpoint used through an SSH tunnel must be addable without changing command semantics.

### 10.3 Explicitly excluded transport

Public webserver to local-worker reverse WebSocket connectivity is not part of this feature and must not be implemented under this feature branch.

## 11. Protocol Compatibility

- Protocol versions MUST use `MAJOR.MINOR` string format, for example `1.0`.
- MVP worker protocol version is exactly `1.0`.
- Same major version `1` is compatible.
- Any different major version MUST be rejected with `INCOMPATIBLE_PROTOCOL`.
- `worker.health` must expose worker protocol version.
- All request envelopes must include client protocol version.

## 12. User Scenarios and Acceptance Tests

### US-001: Web UI opens registered workspace through worker

**Given** a registered workspace exists and no worker is active  
**When** the user starts `ppi serve` and opens that workspace  
**Then** the webserver starts or requests startup of one worker  
**And** connects through the worker boundary  
**And** workspace status is loaded from `analysis.status`  
**And** no direct write to active analysis storage is performed by the webserver.

### US-002: IDE attaches to worker started by webserver

**Given** `ppi serve` already started a worker for workspace `W`  
**When** the IDE extension opens the same workspace `W`  
**Then** the IDE discovers the existing worker  
**And** attaches to it  
**And** does not start a duplicate worker.

### US-003: CLI attaches to existing worker

**Given** a worker is active for workspace `W`  
**When** the user runs a worker-based CLI analysis/status/query command for `W`  
**Then** the CLI attaches to the active worker  
**And** receives a structured response  
**And** does not write directly to the active storage.

### US-004: Multiple clients receive analysis events

**Given** webserver and IDE are subscribed to events for workspace `W`  
**When** analysis starts and emits progress  
**Then** both clients receive live `analysis.started` and `analysis.progress` events  
**And** each client can call `analysis.status` to recover current state if it missed events.

### US-005: Duplicate worker startup is prevented

**Given** no worker is active for workspace `W`  
**When** two clients attempt startup at the same time  
**Then** no more than one worker becomes active writer  
**And** the other client attaches to that worker or receives a clear startup failure.

### US-006: Stale metadata is recovered

**Given** runtime metadata points to a dead worker  
**When** a client tries to connect  
**Then** the client detects failed health check  
**And** marks or treats metadata as `stale`  
**And** starts a new worker if allowed  
**Or** returns a clear remediation message if startup is not allowed.

### US-007: Protocol mismatch is rejected

**Given** client protocol major version differs from worker protocol major version  
**When** the client calls any worker command  
**Then** the worker rejects the request with `INCOMPATIBLE_PROTOCOL`  
**And** the client shows a clear user-facing message.

### US-008: Running analysis is not duplicated

**Given** analysis is already running for workspace `W`  
**When** another client sends `analysis.start`  
**Then** the worker does not start a second analysis  
**And** returns `ok=true`, `accepted=true`, the active run id, and `state=already_running`.

## 13. Functional Requirements

### Worker ownership and clients

- **FR-001**: The system MUST enforce one active writer worker per workspace.
- **FR-002**: The system MUST allow multiple clients to connect to one active worker for the same workspace.
- **FR-003**: CLI, FastAPI/web UI, and IDE integration MUST use the worker boundary for migrated active workspace commands.
- **FR-004**: The webserver MUST NOT write directly to active workspace analysis storage in the worker-based flow.
- **FR-005**: The IDE extension MUST NOT write directly to active workspace analysis storage in the worker-based flow.
- **FR-006**: The CLI MUST use the worker boundary for migrated active analysis/status/query commands.

### Registry and runtime metadata

- **FR-007**: The system MUST maintain workspace registration records with all fields listed in section 4.1.
- **FR-008**: The system MUST maintain runtime metadata with all fields listed in section 4.2.
- **FR-009**: Clients MUST be able to discover whether a worker is available, unavailable, starting, busy, failed, or stale.
- **FR-010**: The system MUST detect stale runtime metadata via process/endpoint health checks before trusting it.
- **FR-011**: The system MUST provide clear diagnostic messages for stale locks, stale endpoints, incompatible protocol versions, startup failures, and unreachable workers.

### Commands

- **FR-012**: The worker MUST implement `worker.health` exactly as described in section 5.2.
- **FR-013**: The worker MUST implement `workspace.info` exactly as described in section 5.2.
- **FR-014**: The worker MUST implement `analysis.status` exactly as described in section 5.2.
- **FR-015**: The worker MUST implement `analysis.start` exactly as described in section 5.2.
- **FR-016**: The worker MUST implement `analysis.cancel` exactly as described in section 5.2.
- **FR-017**: The worker MUST implement `query.execute` exactly as described in section 5.2.
- **FR-018**: The worker MUST implement `events.subscribe` exactly as described in section 5.2.
- **FR-019**: The worker MUST implement `worker.shutdown` exactly as described in section 5.2.
- **FR-020**: Unsupported commands MUST return `UNKNOWN_COMMAND`.
- **FR-021**: Invalid request shapes MUST return `INVALID_REQUEST`.

### Events

- **FR-022**: Worker events MUST use the envelope defined in section 6.1.
- **FR-023**: The worker MUST emit all required event types listed in section 6.2 when the corresponding condition occurs.
- **FR-024**: Event subscription MUST NOT block request/response command handling for other clients.
- **FR-025**: Clients MUST be able to recover current state after reconnect by calling `analysis.status`.

### Errors and compatibility

- **FR-026**: Worker errors MUST use the structured error object defined in section 7.1.
- **FR-027**: The worker MUST support all required error codes listed in section 7.2.
- **FR-028**: Every request MUST include a protocol version.
- **FR-029**: Major protocol version mismatch MUST return `INCOMPATIBLE_PROTOCOL`.
- **FR-030**: `worker.health` MUST return the worker protocol version.

### Lifecycle

- **FR-031**: The system MUST support starting a worker on demand for a registered workspace.
- **FR-032**: The system MUST support attaching to an already-running worker.
- **FR-033**: The system MUST prevent duplicate active writer workers during simultaneous startup attempts.
- **FR-034**: Client disconnects MUST NOT terminate the worker by default.
- **FR-035**: Controlled local shutdown MUST be available through `worker.shutdown`.
- **FR-036**: Worker startup failure MUST be reported to the initiating client with a structured message.
- **FR-037**: Storage consistency MUST be preserved if a client disconnects during analysis.

### Security and boundaries

- **FR-038**: Local IPC endpoints MUST be scoped to the current user or local machine.
- **FR-039**: Worker commands MUST NOT expose unrestricted arbitrary filesystem access.
- **FR-040**: Any future file read/write commands MUST validate paths against the workspace boundary.
- **FR-041**: Remote-worker-over-tunnel compatibility MUST NOT require the worker to listen on a public network interface.
- **FR-042**: Public webserver-to-local-worker reverse connectivity MUST NOT be introduced in this feature.

### Migration

- **FR-043**: Existing direct CLI workflows MUST remain available during this feature unless an individual command explicitly adds and uses `--via-worker`.
- **FR-044**: Any command migrated to worker mode MUST use the same command/event/error model as other worker clients.
- **FR-045**: The implementation MUST provide a visible migration path so users can understand whether a command is using direct legacy mode or worker mode.

## 14. Non-Functional Requirements

- **NFR-001**: Health check for an existing local worker MUST use a 2 second timeout. Worker startup wait MUST use a 10 second timeout. If either timeout expires, the client MUST return a structured error instead of hanging silently.
- **NFR-002**: A failed worker connection attempt MUST fail with a clear error instead of indefinite blocking.
- **NFR-003**: Long-running analysis MUST emit `analysis.progress` at least once per processed commit and at least once every 5 seconds during active work. `analysis.status.message` MUST also reflect the latest progress message.
- **NFR-004**: Runtime files, lock files, and endpoint files MUST be safe to leave behind after crashes because stale recovery is required.
- **NFR-005**: The implementation MUST be testable without requiring a real IDE extension or browser UI; CLI-level and adapter-level tests are acceptable.

## 15. Edge Cases

- Runtime metadata exists but the process is no longer running.
- Runtime endpoint exists but no healthy worker responds.
- Runtime metadata references a worker for a different workspace.
- Two clients attempt to start the same workspace worker at the same time.
- Worker starts but fails before becoming ready.
- Worker becomes ready but runtime metadata update fails.
- Client disconnects during a long analysis run.
- Multiple clients subscribe to events at different times.
- Client has incompatible protocol major version.
- Client sends unknown command.
- Client sends invalid payload for a known command.
- Query request arrives while analysis is running.
- Analysis start request arrives while analysis is already running.
- Cancellation request arrives when no analysis is running.
- Worker crashes while holding write ownership.
- Workspace is moved or deleted after registration.
- Analysis path exists but is incompatible with workspace registration.
- IDE opens a nested folder inside an already registered workspace.
- FastAPI server manages multiple registered workspaces at once.
- CLI is executed from outside the project directory and must resolve workspace identity explicitly.

## 16. Success Criteria

- **SC-001**: In normal local usage, web UI, CLI, and IDE can connect to the same active worker for one workspace without creating duplicate writers.
- **SC-002**: A user can start the web UI and access workspace status/results through the worker boundary for a registered workspace.
- **SC-003**: A user can start or attach to a worker from CLI and receive structured status/progress/failure information.
- **SC-004**: When a worker crashes, `worker status` detects stale runtime state and reports a clear remediation path; `worker start` detects stale runtime state and starts a replacement worker.
- **SC-005**: Existing direct CLI workflows remain available or are clearly identified as legacy during migration.
- **SC-006**: The worker communication layer supports at least one local transport in MVP.
- **SC-007**: Read/query requests and analysis-start requests are routed through the same worker command model.
- **SC-008**: Public-webserver-to-local-worker reverse connectivity remains explicitly outside the implemented IPC scope.
- **SC-009**: A duplicate startup attempt cannot produce two active writer workers for one workspace.
- **SC-010**: Protocol mismatch is rejected with a structured `INCOMPATIBLE_PROTOCOL` error.

## 17. Key Entities

- **Workspace**: Registered project known to PPI, including project path, analysis data path, selected profile, display name, and id.
- **Worker**: Runtime process responsible for one workspace's analysis, queries, events, and storage writes.
- **Client**: CLI, FastAPI adapter, IDE extension, or another process that communicates with the worker.
- **Runtime Metadata**: Discoverable state describing worker endpoint, process id, worker id, protocol version, lifecycle state, and heartbeat.
- **Worker Command**: Request sent by a client to the worker that produces one structured response.
- **Worker Event**: One-way notification emitted by the worker to subscribed clients.
- **Analysis Run**: Worker-managed execution of project analysis with status, progress, diagnostics, and final result.
- **Storage Boundary**: Product rule that active writes to analysis storage are performed only by the workspace worker.

## 18. Assumptions

- MVP usage is local developer-machine usage.
- One workspace corresponds to one active worker and one analysis storage owner.
- Local IPC is the first supported transport.
- Remote worker support, when added, will use SSH tunnel/private connection model rather than public worker exposure.
- FastAPI remains an adapter and does not own project analysis or active storage writes.
- IDE extension remains a bridge/client and does not implement analysis logic.
- Existing CLI behavior can coexist temporarily with worker-based behavior during migration.

## 19. Dependencies

- Existing or minimal workspace registration flow.
- Existing analysis command logic that can be invoked by a worker.
- Existing query logic that can be exposed through `query.execute`.
- Existing storage path conventions for workspace analysis data.
- Existing CLI/FastAPI entry points that can be migrated to the worker boundary.

## 20. Explicit Decisions for Implementers

These decisions are part of the specification to avoid ambiguity:

1. Do not implement public-webserver-to-local-worker reverse connectivity.
2. Do not implement remote Git repository import in this feature.
3. Do not perform a full plugin refactor in this feature.
4. Use the worker as the normal storage writer for active workspace data.
5. Use live events only; event replay is not required for MVP.
6. After reconnect, clients must call `analysis.status` to recover current state.
7. Return successful `analysis.start` with `state=already_running` when analysis is already active. Do not return `ANALYSIS_ALREADY_RUNNING` for this normal duplicate-start case in MVP.
8. Unknown commands and invalid payloads must be structured errors, not crashes.
9. Existing legacy CLI commands MUST remain available during this feature; migrated `--via-worker` commands must use the worker boundary.
10. Use Unix domain sockets as the only implemented transport in this feature. TCP/WSS transports are not implemented in this feature, but command semantics must remain transport-independent.

## 21. Open Questions

No blocking clarification markers remain. This specification is ready for implementation.

## 22. Additional Explicitness Rules for Weak Implementers

- Do not invent a `ready` worker state. Use `idle` for the lifecycle state and `worker.ready` only as an event type emitted when startup completes.
- Do not invent query names. The query whitelist is the current `ppi.query.dispatch.QueryMethod` value list copied into `plan.md` and `contracts/protocol.md`; update both only if the repository enum changes.
- Do not return raw dispatcher objects through IPC. Convert to JSON-compatible `columns`, `rows`, `row_count`, and `truncated` exactly as specified for `query.execute`.
- Do not add `--workspace`, TCP, WSS, public networking, event replay, or direct browser-to-worker communication.
- Do not skip stale metadata health checks. Metadata is advisory until `worker.health` succeeds.
