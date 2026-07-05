# Contract: CLI Worker Commands

The existing CLI uses global `--repo`, `--branch`, `--profile`, and `--analysis-dir` options. Do not introduce a separate `--workspace` option in this feature. Workspace id is derived from `--repo` with `project_id_from_repo`.

## 1. Start worker

```bash
ppi --repo /abs/path/project worker start
```

Expected behavior:

- resolves repo using existing global CLI context;
- registers or updates workspace in `~/.local/share/ppi/workspaces.json`;
- if a healthy worker exists, prints the existing worker id and endpoint;
- otherwise spawns `worker run`;
- waits up to 10 seconds for `worker.health`;
- exits 0 when worker is healthy;
- exits non-zero with structured message when startup fails.

JSON output when `--json` is passed to `worker start`:

```json
{
  "ok": true,
  "workspace_id": "d34db33fd34db33f",
  "worker_id": "worker-xyz",
  "state": "idle",
  "endpoint": "unix:///tmp/ppi/1000/d34db33fd34db33f/worker.sock",
  "protocol_version": "1.0"
}
```

## 2. Worker status

```bash
ppi --repo /abs/path/project worker status
```

Expected behavior:

- registers or updates workspace;
- reads metadata;
- performs `worker.health` if metadata exists;
- reports one of `healthy`, `stale`, `unavailable`, `incompatible_protocol`, or `workspace_mismatch`;
- does not start worker.

## 3. Stop worker

```bash
ppi --repo /abs/path/project worker stop
```

Expected behavior:

- attaches only to a healthy worker;
- sends `worker.shutdown`;
- if worker is busy, exits non-zero and prints `WORKER_BUSY`;
- if no worker exists, exits 0 with a clear "no active worker" message.

## 4. Internal foreground worker

```bash
ppi --repo /abs/path/project worker run
```

Expected behavior:

- starts the Unix socket server in the foreground;
- writes runtime metadata;
- updates heartbeat every 5 seconds;
- exits when `worker.shutdown` succeeds or on fatal error;
- this command is hidden from normal help if the CLI framework supports hidden commands.

## 5. Analysis through worker

```bash
ppi --repo /abs/path/project analyze --via-worker
ppi --repo /abs/path/project analyze --via-worker --rebuild
```

Mapping:

- without `--rebuild`: `analysis.start` payload `{"mode":"incremental","reason":"cli"}`;
- with `--rebuild`: `analysis.start` payload `{"mode":"full","reason":"cli"}`.

Expected behavior:

- starts or attaches worker;
- sends `analysis.start`;
- if response state is `running`, prints run id and follows progress by events or status polling;
- if response state is `already_running`, prints active run id and does not start another run;
- exits non-zero only on structured worker error.

## 6. Query through worker

```bash
ppi --repo /abs/path/project query --via-worker --metric project-info --format json
ppi --repo /abs/path/project query --via-worker --metric snapshot-table-modules --format json
```

Expected behavior:

- maps existing CLI metric to existing query method using current `_cli_metric_to_method` mapping, including `project-info -> project/info` and `snapshot-table-modules -> snapshot/table/modules`;
- sends `query.execute`;
- prints JSON/table/CSV using the same output rules as legacy `query`;
- unknown query returns `UNKNOWN_QUERY`.

## 7. Legacy mode visibility

Existing direct `analyze`, `query`, and `serve` behavior MUST remain for migration safety. Help text must make worker mode explicit:

```text
--via-worker  Route this command through the workspace worker IPC boundary.
```
