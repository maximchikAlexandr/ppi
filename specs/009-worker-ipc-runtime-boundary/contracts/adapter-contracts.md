# Contract: FastAPI and IDE Adapter Behavior

## 1. Shared rule

Adapters must not implement separate analysis orchestration or active storage writes for worker-backed flows. They must use `WorkerGateway` and `WorkerClient` from `src/ppi/worker_ipc`.

## 2. FastAPI MVP scope

Do not rewrite the frontend in this feature. Add worker-backed backend endpoints under `/api/worker` and keep legacy dashboard endpoints available.

Required endpoints:

| HTTP endpoint | Worker command |
|---|---|
| `GET /api/worker/health` | `worker.health` |
| `GET /api/worker/workspace` | `workspace.info` |
| `GET /api/worker/analysis/status` | `analysis.status` |
| `POST /api/worker/analysis/start` | `analysis.start` |
| `POST /api/worker/analysis/cancel` | `analysis.cancel` |
| `POST /api/worker/query` | `query.execute` |

Rules:

- `ppi serve` must start or attach a worker before creating the app.
- `src/ppi/server/app.py` must accept an optional worker gateway/client dependency for worker endpoints.
- Worker structured errors must be translated to HTTP JSON without losing `code`, `message`, `details`, or `recoverable`.
- Existing direct store endpoints MUST remain for legacy dashboard compatibility in this feature.

## 3. IDE MVP scope

Do not rewrite the VS Code extension in this feature.

Provide stable CLI/IPC behavior that the extension documentation can rely on during this feature:

```text
ppi --repo <workspace-folder> worker status
ppi --repo <workspace-folder> worker start
ppi --repo <workspace-folder> analyze --via-worker
```

Rules the extension migration must follow when it is implemented:

- resolve current workspace from IDE folder;
- attach to existing worker if webserver/CLI already started it;
- start worker only if no healthy worker exists;
- do not start duplicate writer;
- use `analysis.status` after reconnect because there is no event replay.

## 4. Multi-client behavior

When FastAPI and CLI are both connected:

- each client can call `analysis.status`;
- only one analysis run can be active;
- if both clients call `analysis.start`, one run exists and the second receives `ok=true`, `state=already_running`;
- subscribed clients receive live events;
- disconnecting one client does not stop the worker.
