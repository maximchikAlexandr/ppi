# Data Model: Worker IPC Runtime Boundary

This file defines runtime and protocol entities for implementation. It is not the analytics domain model.

## 1. WorkspaceRegistration

Represents a project known to PPI.

| Field | Type | Required | Validation |
|---|---|---:|---|
| `workspace_id` | string | yes | Exactly `project_id_from_repo(project_path)` for this feature. |
| `project_path` | absolute path string | yes | Must be absolute. May be missing on disk only if reported clearly. |
| `analysis_path` | absolute path string | yes | Must be absolute. Parent must be creatable or existing. |
| `profile` | string | yes | Non-empty. Examples: `python`, `odoo`. |
| `display_name` | string | yes | Non-empty. |
| `created_at` | ISO-8601 timestamp | yes | UTC required. |
| `updated_at` | ISO-8601 timestamp | yes | Must update when registration changes. |

Relationships:

- One WorkspaceRegistration has zero or one current RuntimeMetadata record.
- One WorkspaceRegistration may have many AnalysisRun records over time.

## 2. RuntimeMetadata

Describes the current or last known worker process for a workspace.

| Field | Type | Required | Validation |
|---|---|---:|---|
| `workspace_id` | string | yes | Must match WorkspaceRegistration. |
| `worker_id` | string | yes | Unique for one worker process lifetime. |
| `pid` | integer | yes | Required for MVP local Unix worker. Do not use null in this feature. |
| `endpoint` | string | yes | Endpoint URI, MVP `unix://...`. |
| `transport` | string | yes | Exact MVP value `unix`. Do not write `tcp` in this feature. |
| `protocol_version` | string | yes | Format `MAJOR.MINOR`, e.g. `1.0`. |
| `state` | WorkerState | yes | See WorkerState. |
| `started_at` | ISO-8601 timestamp | yes | Worker start time. |
| `updated_at` | ISO-8601 timestamp | yes | Last metadata write time. |
| `last_heartbeat_at` | ISO-8601 timestamp | yes | Last heartbeat time. |
| `last_error` | object/null | no | Optional diagnostic object for failed startup/runtime. When present, it uses worker error fields `code`, `message`, `details`, `recoverable`. |

State rules:

- Metadata is advisory and must not be trusted without `worker.health`.
- Metadata can remain after crashes and discovery MUST handle it as advisory only.
- Discovery MUST mark metadata `stale` if health check fails.

## 3. WorkerState

Allowed values:

```text
starting
idle
busy
stopping
stopped
failed
stale
```

Note: No `ready` state exists in MVP. Healthy ready/no-work state is always `idle`. If legacy code emits `ready`, treat it as a bug and map it to `idle` only at compatibility boundaries.

Transitions:

| From | To | Trigger |
|---|---|---|
| `starting` | `idle` | Initialization complete. |
| `starting` | `failed` | Initialization failure. |
| `idle` | `busy` | Analysis or exclusive operation starts. |
| `busy` | `idle` | Operation completed/failed/cancelled safely. |
| `idle` | `stopping` | Shutdown accepted. |
| `busy` | `stopping` | Graceful shutdown accepted after safe cancellation/wait. |
| `stopping` | `stopped` | Worker exits normally. |
| any | `failed` | Runtime fatal error. |
| any metadata | `stale` | Client-side health check fails for old metadata. |

## 4. WorkerRequest

| Field | Type | Required | Validation |
|---|---|---:|---|
| `request_id` | string | yes | Non-empty, unique per client request. |
| `protocol_version` | string | yes | Same major version required. |
| `workspace_id` | string | yes | Must match worker workspace. |
| `command` | string | yes | Must be a known command. |
| `payload` | object | yes | Command-specific object. Empty object allowed. |

## 5. WorkerResponse

| Field | Type | Required | Validation |
|---|---|---:|---|
| `request_id` | string | yes | Must match request. |
| `ok` | bool | yes | True for success. |
| `result` | object/null | yes | Required object when `ok=true`; null when `ok=false`. |
| `error` | WorkerError/null | yes | Required object when `ok=false`; null when `ok=true`. |

## 6. WorkerError

| Field | Type | Required | Validation |
|---|---|---:|---|
| `code` | string | yes | One of required error codes. |
| `message` | string | yes | Human-readable, non-empty. |
| `details` | object/null | no | Structured diagnostic context only. |
| `recoverable` | bool | yes | Retry/remediation hint. |

Required codes:

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

## 7. WorkerEvent

| Field | Type | Required | Validation |
|---|---|---:|---|
| `event_id` | string | yes | Unique. |
| `workspace_id` | string | yes | Must match worker workspace. |
| `worker_id` | string | yes | Current worker id. |
| `event_type` | string | yes | One of required event types. |
| `created_at` | ISO-8601 timestamp | yes | UTC required. |
| `payload` | object | yes | Event-specific object. |

Required event types:

```text
worker.ready
worker.state_changed
worker.warning
worker.failed
analysis.started
analysis.progress
analysis.warning
analysis.completed
analysis.cancelled
analysis.failed
```

## 8. AnalysisRunStatus

Represents current worker-known analysis state.

| Field | Type | Required | Validation |
|---|---|---:|---|
| `state` | string | yes | `not_started`, `running`, `completed`, `failed`, `cancelled`. |
| `current_run_id` | string/null | yes | Non-null only when active run exists. |
| `last_run_id` | string/null | yes | Most recent known run id. |
| `progress_percent` | number/null | yes | 0..100 when measurable. |
| `message` | string | yes | User-readable status. |

Transitions:

```text
not_started -> running -> completed
not_started -> running -> failed
not_started -> running -> cancelled
completed -> running
failed -> running
cancelled -> running
```

## 9. Subscription

In-memory runtime object only. It does not need persistent storage.

| Field | Type | Required | Validation |
|---|---|---:|---|
| `subscription_id` | string | yes | Unique within worker process. |
| `client_id` | string | yes | Connection/client identifier. |
| `event_types` | list[string]/null | no | Null means all event types. |
| `created_at` | timestamp | yes | Subscription creation time. |

## 10. StartupLock

Represents a per-workspace lock used during worker startup.

| Field | Type | Required | Validation |
|---|---|---:|---|
| `workspace_id` | string | yes | Target workspace. |
| `lock_path` | absolute path string | yes | Workspace or runtime lock file path. |
| `owner_pid` | integer | yes | Process attempting startup. |
| `created_at` | timestamp | yes | Lock creation time. |

Rules:

- Lock must be released after startup attempt completes.
- If lock owner pid is dead, recovery MUST remove/replace it after diagnostics.
- After acquiring lock, always re-check for a healthy worker before spawning.
