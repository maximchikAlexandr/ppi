# Contract: Workspace Registry and Runtime Files

## 1. Workspace registry

Use one JSON registry file for this feature:

```text
~/.local/share/ppi/workspaces.json
```

Tests MUST override it with a temporary path:

```text
PPI_WORKSPACE_REGISTRY=/tmp/ppi-test-workspaces.json
```

Workspace id is derived from the canonical repo path with the existing function:

```text
ppi.runtime.paths.project_id_from_repo(repo_path)
```

Record shape:

```json
{
  "workspace_id": "d34db33fd34db33f",
  "project_path": "/abs/path/project",
  "analysis_path": "/home/user/.local/share/ppi/d34db33fd34db33f",
  "profile": "odoo",
  "display_name": "project",
  "created_at": "2026-07-04T12:00:00Z",
  "updated_at": "2026-07-04T12:00:00Z"
}
```

Required operations in `src/ppi/worker_ipc/registry.py`:

```text
registry_path() -> Path
load_registry() -> dict[str, WorkspaceRegistration]
save_registry(records) -> None
register_or_update_from_repo(repo, analysis_dir, profile) -> WorkspaceRegistration
get_workspace(workspace_id) -> WorkspaceRegistration | None
resolve_workspace_from_repo(repo) -> WorkspaceRegistration | None
list_workspaces() -> list[WorkspaceRegistration]
```

## 2. Runtime directory

Use these exact runtime paths:

```text
runtime_root = $XDG_RUNTIME_DIR/ppi              if XDG_RUNTIME_DIR is set
runtime_root = /tmp/ppi/<uid>                    otherwise
runtime_dir  = <runtime_root>/<workspace_id>
socket       = <runtime_dir>/worker.sock
metadata     = <runtime_dir>/worker.json
startup_lock = <runtime_dir>/worker.lock
```

The implementation must create `runtime_dir` with mode `0700` when the platform supports chmod.

## 3. Runtime metadata

`worker.json` content:

```json
{
  "workspace_id": "d34db33fd34db33f",
  "worker_id": "uuid-or-hex-id",
  "pid": 12345,
  "endpoint": "unix:///tmp/ppi/1000/d34db33fd34db33f/worker.sock",
  "transport": "unix",
  "protocol_version": "1.0",
  "state": "idle",
  "started_at": "2026-07-04T12:00:00Z",
  "updated_at": "2026-07-04T12:00:05Z",
  "last_heartbeat_at": "2026-07-04T12:00:05Z",
  "last_error": null
}
```

Valid states:

```text
starting
idle
busy
stopping
stopped
failed
stale
```

No `ready` state is persisted. A healthy ready/no-work worker is `idle`.

## 4. Startup lock

Startup lock path:

```text
<runtime_dir>/worker.lock
```

Rules:

1. Gateway acquires this lock before spawning `worker run`.
2. Gateway repeats metadata + health check after acquiring the lock.
3. If a healthy worker exists after the re-check, gateway releases the lock and attaches.
4. If no healthy worker exists, gateway spawns exactly one worker process.
5. Gateway releases the lock after worker becomes healthy or startup fails.
6. If lock holder pid is dead, lock recovery MUST remove it using the same stale-pid logic as `ppi.runtime.lock`.

## 5. Socket endpoint

Endpoint URI format:

```text
unix://<absolute socket path>
```

Examples:

```text
unix:///run/user/1000/ppi/d34db33fd34db33f/worker.sock
unix:///tmp/ppi/1000/d34db33fd34db33f/worker.sock
```

Rules:

- Worker listens only on Unix domain socket in this feature.
- Remove stale socket file only after `worker.health` fails.
- Do not implement TCP or WSS endpoint parsing beyond returning `unsupported transport` diagnostics.

## 6. Metadata trust rules

Runtime metadata is not authoritative by itself.

Discovery must always:

1. read metadata;
2. attempt `worker.health` with 2 second timeout;
3. verify returned `workspace_id` matches the requested workspace;
4. verify protocol major version is `1`;
5. only then attach.

If any check fails, metadata is stale or invalid.
