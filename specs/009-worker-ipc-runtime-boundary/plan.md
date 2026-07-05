# Implementation Plan: Worker IPC Runtime Boundary

**Feature**: `009-worker-ipc-runtime-boundary`  
**Spec**: `specs/009-worker-ipc-runtime-boundary/spec.md`  
**Created**: 2026-07-04  
**Updated**: 2026-07-05  
**Status**: Ready for tasks

## 1. Goal

Introduce a stable worker IPC/runtime boundary for PPI so CLI, FastAPI/web UI, and IDE integration communicate with one active workspace worker instead of directly controlling analysis or writing analysis storage.

This implementation plan is intentionally prescriptive. The implementing model must follow the selected module layout, command names, file locations, timeouts, and MVP behavior below. Do not substitute alternative transports, protocols, registries, or command semantics.

## 2. Current Repository Facts Used by This Plan

The current repository has these relevant paths:

- `src/ppi/cli/main.py` contains the `click` CLI, including `analyze`, `query`, `serve`, `openapi`, `rpc`, and `doctor` commands.
- `src/ppi/runtime/paths.py` already contains project id, analysis directory, `.ppi/history.duckdb`, worktree, and writer-lock path helpers.
- `src/ppi/runtime/lock.py` already contains a PID-based stale-lock-aware file lock implementation.
- `src/ppi/query/dispatch.py` already contains the read query dispatcher and the stable query method names.
- `src/ppi/server/app.py` currently creates a FastAPI app around direct store/lock paths.

## 3. Exact MVP Scope

Implement only these items:

1. Local Unix-socket worker IPC.
2. `msgspec` MessagePack request/response/event structs.
3. 4-byte unsigned big-endian length-prefixed frames.
4. One worker process per workspace.
5. Startup lock and runtime metadata.
6. CLI worker lifecycle commands.
7. Worker-backed `analysis.start`, `analysis.status`, `analysis.cancel`, and `query.execute`.
8. Worker-backed FastAPI endpoints under `/api/worker/*`.
9. Contract, unit, and integration tests.

Do not implement:

- TCP transport.
- WebSocket reverse connector.
- Public webserver to local worker.
- Remote Git repository import.
- Full plugin refactor.
- Full frontend rewrite.
- Full VS Code extension rewrite.
- Persistent event replay.

## 4. Selected Module Layout

Create a new package and use these exact files:

```text
src/ppi/worker_ipc/
  __init__.py
  constants.py
  protocol.py
  framing.py
  endpoint.py
  unix_transport.py
  client.py
  events.py
  runtime_paths.py
  registry.py
  runtime_metadata.py
  locks.py
  supervisor.py
  gateway.py
  server.py
  worker_runtime.py
  analysis_service.py
  query_service.py
  cli_handlers.py
```

Do not put IPC protocol code into `src/ppi/server`, `src/ppi/query`, or `vscode-extension`.

## 5. Constants

`src/ppi/worker_ipc/constants.py` must define:

```text
PROTOCOL_VERSION = "1.0"
PROTOCOL_MAJOR = 1
MAX_FRAME_BYTES = 16_777_216
HEARTBEAT_INTERVAL_SECONDS = 5.0
HEALTH_CHECK_TIMEOUT_SECONDS = 2.0
WORKER_START_TIMEOUT_SECONDS = 10.0
CLIENT_COMMAND_TIMEOUT_SECONDS = 30.0
EVENT_QUEUE_MAXSIZE = 100
```

## 6. Protocol and Encoding

Use `msgspec.Struct` in `src/ppi/worker_ipc/protocol.py`.

Required enums:

```text
WorkerState: starting, idle, busy, stopping, stopped, failed, stale
AnalysisState: not_started, running, completed, failed, cancelled
WorkerCommand: worker.health, workspace.info, analysis.status, analysis.start, analysis.cancel, query.execute, events.subscribe, worker.shutdown
WorkerEventType: worker.ready, worker.state_changed, worker.warning, worker.failed, analysis.started, analysis.progress, analysis.warning, analysis.completed, analysis.cancelled, analysis.failed
WorkerErrorCode: INVALID_REQUEST, UNKNOWN_COMMAND, INCOMPATIBLE_PROTOCOL, WORKSPACE_MISMATCH, WORKER_NOT_READY, WORKER_BUSY, ANALYSIS_ALREADY_RUNNING, NO_ACTIVE_ANALYSIS, UNKNOWN_QUERY, QUERY_FAILED, STORAGE_UNAVAILABLE, INTERNAL_ERROR
```

`worker.ready` is an event type only. Do not add `ready` to `WorkerState`; the event payload state is exactly `idle`.

Required structs:

```text
WorkerRequest(request_id, protocol_version, workspace_id, command, payload)
WorkerResponse(request_id, ok, result, error)
WorkerError(code, message, details, recoverable)
WorkerEvent(event_id, workspace_id, worker_id, event_type, created_at, payload)
WorkspaceInfo(workspace_id, project_path, analysis_path, profile, display_name)
AnalysisStatus(state, current_run_id, last_run_id, progress_percent, message)
```

Payload/result structs MUST only be added when they directly implement the command payloads/results listed in `contracts/protocol.md`; the request/response/event envelope fields must remain exactly as specified.

## 7. Framing

`src/ppi/worker_ipc/framing.py` must implement one shared framing layer for client and server:

```text
read_frame(reader) -> bytes
write_frame(writer, payload: bytes) -> None
```

Rules:

- first 4 bytes are unsigned big-endian payload length;
- reject length > `MAX_FRAME_BYTES`;
- raise a deterministic frame error on incomplete frames;
- support multiple frames on one stream;
- do not use newline-delimited messages.

## 8. Endpoint and Runtime Files

Use these exact runtime paths:

```text
runtime_root = $XDG_RUNTIME_DIR/ppi              if XDG_RUNTIME_DIR is set
runtime_root = /tmp/ppi/<uid>                    otherwise
runtime_dir  = <runtime_root>/<workspace_id>
socket       = <runtime_dir>/worker.sock
metadata     = <runtime_dir>/worker.json
startup_lock = <runtime_dir>/worker.lock
```

The implementation must create `runtime_dir` with mode `0700` where supported.

Runtime metadata JSON fields:

```json
{
  "workspace_id": "...",
  "worker_id": "...",
  "pid": 123,
  "endpoint": "unix:///tmp/ppi/1000/<workspace_id>/worker.sock",
  "transport": "unix",
  "protocol_version": "1.0",
  "state": "idle",
  "started_at": "2026-07-04T12:00:00Z",
  "updated_at": "2026-07-04T12:00:05Z",
  "last_heartbeat_at": "2026-07-04T12:00:05Z",
  "last_error": null
}
```

Metadata is advisory. Gateway must call `worker.health` before trusting metadata.

## 9. Workspace Registry

Implement `src/ppi/worker_ipc/registry.py` as a JSON registry file:

```text
~/.local/share/ppi/workspaces.json
```

Test override:

```text
PPI_WORKSPACE_REGISTRY=/tmp/some-test-workspaces.json
```

Use `ppi.runtime.paths.project_id_from_repo(repo)` as `workspace_id`. Register/update the workspace whenever a worker-backed command resolves a repo.

Required record fields:

```text
workspace_id, project_path, analysis_path, profile, display_name, created_at, updated_at
```

Do not introduce SQLite in this feature.

## 10. Startup and Discovery

`src/ppi/worker_ipc/gateway.py` must implement this exact flow:

```text
resolve repo/profile/analysis_dir to WorkspaceRegistration
register_or_update workspace
read runtime metadata
if metadata exists: health-check endpoint with 2 second timeout
if healthy and workspace/protocol match: return WorkerClient
if startup not allowed: return unavailable/stale diagnostic
if startup allowed: acquire startup lock
inside lock: repeat metadata + health-check
if healthy after re-check: return WorkerClient
spawn worker process via Supervisor
wait up to 10 seconds for worker.health
if healthy: return WorkerClient
else: return structured startup failure
```

No branch may spawn a second worker without first acquiring the startup lock and re-checking health.

## 11. CLI Commands

Because the existing CLI requires global `--repo`, use these exact public commands:

```bash
ppi --repo /path/to/repo worker start
ppi --repo /path/to/repo worker status
ppi --repo /path/to/repo worker stop
ppi --repo /path/to/repo worker run       # internal/hidden foreground worker command
ppi --repo /path/to/repo analyze --via-worker
ppi --repo /path/to/repo query --via-worker --metric project-info --format json
ppi --repo /path/to/repo query --via-worker --metric snapshot-table-modules --format json
```

Do not implement a separate `--workspace` CLI option in this feature. Workspace id is derived from `--repo` using existing `project_id_from_repo`.

`worker run` is the actual long-lived worker process. `worker start` spawns `worker run` using `subprocess.Popen` and then waits for `worker.health`.

## 12. Analysis Semantics

`analysis.start` payload:

```json
{"mode": "full", "reason": "cli"}
```

Exact MVP behavior:

- `mode=full` maps to current `analyze --rebuild` behavior.
- `mode=incremental` maps to current default incremental behavior.
- If no analysis is running, start one background task in the worker and return `ok=true`, `accepted=true`, `state=running`, `run_id=<new id>`.
- If analysis is already running, do not start a second run. Return `ok=true`, `accepted=true`, `state=already_running`, and the active `run_id`.
- Do not return `ANALYSIS_ALREADY_RUNNING` for normal duplicate start.
- Worker state is `busy` during analysis and `idle` after completion/failure/cancellation.
- `analysis.cancel` sets a cooperative cancellation flag. If the existing analysis code cannot stop mid-run yet, cancellation must be accepted but take effect at the next safe checkpoint. The status message must say cancellation is pending until the run actually stops.

## 13. Query Semantics

Use the existing query names from `ppi.query.dispatch.QueryMethod` as the only allowed `query_name` values. For the current repository snapshot, copy this exact value list into `query_service.py` tests and keep it synchronized with the enum:

```text
commits
metrics/timeseries
hotspots
graph
ui/config
snapshot/table/modules
snapshot/table/files
snapshot/relations
project/info
```

Rules:

- Unknown query returns `UNKNOWN_QUERY`. The current accepted names are exactly the list above because they are present in `QueryMethod`; legacy or invented names such as `catalog`, `snapshot/modules`, `snapshot/files`, `raw/sql`, and `snapshot/table/unknown` MUST return `UNKNOWN_QUERY`.
- While analysis is running, every `query.execute` returns `WORKER_BUSY`.
- When analysis is not running, open the store read-only and call existing `ppi.query.dispatch.dispatch`.
- Convert Pydantic results with `model_dump(mode="json")` before returning through msgspec whenever the result object has `model_dump`. Normalize results to `{columns, rows, row_count, truncated}`: dict/object => one row; list => list rows; scalar => one row `{"value": scalar}`; apply optional `limit` after normalization.

## 14. Event Semantics

Use live in-memory events only. No replay.

Rules:

- Each subscribed client receives only future events.
- After reconnect, clients call `analysis.status`.
- Each subscriber has an async queue of max size `EVENT_QUEUE_MAXSIZE`.
- If a subscriber queue is full, disconnect that subscriber and emit `worker.warning` to remaining subscribers.
- Broadcast must never block analysis execution.

## 15. FastAPI Scope

Do not rewrite the frontend in this feature.

Add worker-backed backend endpoints under `/api/worker`:

```text
GET  /api/worker/health
GET  /api/worker/workspace
GET  /api/worker/analysis/status
POST /api/worker/analysis/start
POST /api/worker/analysis/cancel
POST /api/worker/query
```

Existing legacy dashboard endpoints MUST remain. The new endpoints prove the worker-backed adapter boundary.

## 16. Testing Strategy

Add tests under:

```text
tests/worker_ipc/
```

Required groups:

- protocol tests;
- framing tests;
- runtime path and metadata tests;
- registry tests;
- gateway/supervisor race tests;
- worker server/client integration tests;
- CLI worker command tests;
- FastAPI worker endpoint tests.

Do not require a real IDE, browser UI, TCP port, public server, or remote Git repository for tests.

## 17. Constitution Check

`.specify/memory/constitution.md` exists and was reviewed on 2026-07-05. This feature follows the required CLI-first multi-interface shape, single-writer ownership, typed contracts, explicit worker errors, and local IPC boundary. The constitution intentionally defines only a global local workspace registry role; this feature fixes the concrete MVP storage to JSON at `~/.local/share/ppi/workspaces.json` and explicitly forbids SQLite for this feature.

## 18. Risks and Mitigations

| Risk | Mandatory mitigation |
|---|---|
| Duplicate writer workers | Startup lock + health re-check inside lock + worker id metadata |
| Stale socket/metadata | Metadata health-check before trust; stale metadata overwritten only after failed health check |
| Slow/broken event subscriber | Per-subscriber bounded queue; disconnect slow subscriber |
| Worker process startup ambiguity | Only `worker run` serves; only `worker start` spawns; hidden internal command is documented |
| Query/storage concurrency | `query.execute` returns `WORKER_BUSY` while analysis is running |
| Weak implementer guessing behavior | Follow `tasks.md` sequentially; no alternative transports or CLI shapes |

## 19. Next Phase

Implement `tasks.md` exactly in task ID order, using parallel tasks only where explicitly marked `[P]`.
