# Contract: Worker IPC Protocol

## 1. Protocol version

MVP protocol version is exactly:

```text
1.0
```

Compatibility rule:

- request `protocol_version` must be a string in `MAJOR.MINOR` format;
- major version `1` is accepted;
- any other major version returns `INCOMPATIBLE_PROTOCOL`;
- minor version is ignored in MVP if major is `1` and required fields are present.

## 2. Encoding and framing

Each message frame:

```text
uint32_be payload_length
payload_length bytes of msgspec MessagePack payload
```

Maximum frame size:

```text
16777216 bytes
```

## 3. Request envelope

```json
{
  "request_id": "req-123",
  "protocol_version": "1.0",
  "workspace_id": "d34db33fd34db33f",
  "command": "worker.health",
  "payload": {}
}
```

Required commands:

```text
worker.health
workspace.info
analysis.status
analysis.start
analysis.cancel
query.execute
events.subscribe
worker.shutdown
```

## 4. Successful response envelope

```json
{
  "request_id": "req-123",
  "ok": true,
  "result": {},
  "error": null
}
```

## 5. Error response envelope

```json
{
  "request_id": "req-123",
  "ok": false,
  "result": null,
  "error": {
    "code": "UNKNOWN_COMMAND",
    "message": "Unsupported worker command: example.missing",
    "details": {"command": "example.missing"},
    "recoverable": false
  }
}
```

## 6. Event envelope

```json
{
  "event_id": "evt-123",
  "workspace_id": "d34db33fd34db33f",
  "worker_id": "worker-xyz",
  "event_type": "analysis.progress",
  "created_at": "2026-07-04T12:00:00Z",
  "payload": {
    "run_id": "run-1",
    "progress_percent": 42.0,
    "message": "Analyzed 42% of commits"
  }
}
```

## 7. Commands

### 7.1 `worker.health`

Request payload:

```json
{}
```

Success result:

```json
{
  "worker_id": "worker-xyz",
  "workspace_id": "d34db33fd34db33f",
  "protocol_version": "1.0",
  "state": "idle",
  "started_at": "2026-07-04T12:00:00Z"
}
```

### 7.2 `workspace.info`

Request payload:

```json
{}
```

Success result:

```json
{
  "workspace_id": "d34db33fd34db33f",
  "project_path": "/abs/path/project",
  "analysis_path": "/home/user/.local/share/ppi/d34db33fd34db33f",
  "profile": "odoo",
  "display_name": "project"
}
```

### 7.3 `analysis.status`

Request payload:

```json
{}
```

Success result:

```json
{
  "state": "running",
  "current_run_id": "run-1",
  "last_run_id": "run-1",
  "progress_percent": 31.5,
  "message": "Analyzing commits"
}
```

Allowed states:

```text
not_started
running
completed
failed
cancelled
```

### 7.4 `analysis.start`

Request payload:

```json
{
  "mode": "incremental",
  "reason": "cli"
}
```

Allowed mode values:

```text
full
incremental
```

Success result when new run starts:

```json
{
  "run_id": "run-1",
  "accepted": true,
  "state": "running",
  "message": "Analysis started"
}
```

Mandatory success result when analysis is already running:

```json
{
  "run_id": "run-1",
  "accepted": true,
  "state": "already_running",
  "message": "Analysis is already running"
}
```

The MVP must not return `ANALYSIS_ALREADY_RUNNING` for this normal duplicate-start case.

### 7.5 `analysis.cancel`

Request payload:

```json
{
  "run_id": "run-1",
  "reason": "user requested cancellation"
}
```

If no active run:

```json
{
  "accepted": false,
  "run_id": null,
  "message": "No active analysis to cancel"
}
```

If active run exists:

```json
{
  "accepted": true,
  "run_id": "run-1",
  "message": "Cancellation requested"
}
```

### 7.6 `query.execute`

Request payload:

```json
{
  "query_name": "snapshot/table/modules",
  "parameters": {},
  "limit": 100
}
```

Allowed query names for the current repository snapshot. These MUST match `ppi.query.dispatch.QueryMethod` values exactly:

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

Success result:

```json
{
  "columns": [],
  "rows": [
    {"project_id": "d34db33fd34db33f", "branch": "main", "commit_count": 123}
  ],
  "row_count": 1,
  "truncated": false
}
```

Rules:

- Unknown query returns `UNKNOWN_QUERY`. Names not present in the current enum, such as `catalog`, `snapshot/modules`, `snapshot/files`, `raw/sql`, and `snapshot/table/unknown`, MUST return `UNKNOWN_QUERY` unless the repository enum explicitly adds them later.
- While analysis is running, every query returns `WORKER_BUSY`.
- Result normalization is deterministic: dispatcher dict/object => one row; dispatcher list => rows list; scalar => one row with key `value`; `columns` is the ordered union of object keys; `row_count` counts returned rows; `truncated` is true only when request `limit` omits rows.
- No raw SQL command exists in MVP.

### 7.7 `events.subscribe`

Request payload for all events:

```json
{}
```

Request payload for selected events:

```json
{
  "event_types": ["analysis.started", "analysis.progress", "analysis.completed", "analysis.failed"]
}
```

Success result:

```json
{
  "subscription_id": "sub-1",
  "accepted_event_types": ["analysis.started", "analysis.progress", "analysis.completed", "analysis.failed"]
}
```

### 7.8 `worker.shutdown`

Request payload:

```json
{
  "reason": "user requested stop"
}
```

Success result when idle:

```json
{
  "accepted": true,
  "message": "Worker shutdown accepted"
}
```

If busy:

```json
{
  "request_id": "req-stop-1",
  "ok": false,
  "result": null,
  "error": {
    "code": "WORKER_BUSY",
    "message": "Worker is running analysis and cannot shut down safely",
    "details": {"current_run_id": "run-1"},
    "recoverable": true
  }
}
```

## 8. Required error codes

```text
INVALID_REQUEST
UNKNOWN_COMMAND
INCOMPATIBLE_PROTOCOL
WORKSPACE_MISMATCH
WORKER_NOT_READY
WORKER_BUSY
ANALYSIS_ALREADY_RUNNING
NO_ACTIVE_ANALYSIS
UNKNOWN_QUERY
QUERY_FAILED
STORAGE_UNAVAILABLE
INTERNAL_ERROR
```

`ANALYSIS_ALREADY_RUNNING` is reserved for compatibility and is not used for normal duplicate `analysis.start` in MVP.

## 9. Required event payloads

### `worker.ready`

```json
{"state": "idle"}
```

### `worker.state_changed`

```json
{"previous_state": "idle", "state": "busy"}
```

### `worker.warning`

```json
{"message": "Warning text", "code": "WARNING_CODE"}
```

### `worker.failed`

```json
{"message": "Failure text", "code": "INTERNAL_ERROR"}
```

### `analysis.started`

```json
{"run_id": "run-1", "mode": "incremental"}
```

### `analysis.progress`

```json
{"run_id": "run-1", "progress_percent": 50.0, "message": "Half done"}
```

### `analysis.warning`

```json
{"run_id": "run-1", "message": "Warning text", "code": "WARNING_CODE"}
```

### `analysis.completed`

```json
{"run_id": "run-1", "message": "Analysis completed"}
```

### `analysis.cancelled`

```json
{"run_id": "run-1", "message": "Analysis cancelled"}
```

### `analysis.failed`

```json
{"run_id": "run-1", "message": "Analysis failed", "code": "INTERNAL_ERROR"}
```
