# Quickstart: Worker IPC Runtime Boundary Validation

This quickstart describes manual validation scenarios for the implementation.

## 1. Prerequisites

- PPI project installed in editable/dev mode.
- Unix-like environment for MVP Unix socket transport.
- A local test repository exists.

Example:

```bash
export PPI_TEST_PROJECT=/abs/path/to/test-project
```

## 2. Start worker

```bash
ppi --repo "$PPI_TEST_PROJECT" worker start --json
```

Expected:

- command exits 0;
- JSON contains `ok=true`, `worker_id`, `workspace_id`, `endpoint`, `protocol_version=1.0`, `state=idle`;
- runtime metadata exists at `/tmp/ppi/<uid>/<workspace_id>/worker.json` if `XDG_RUNTIME_DIR` is not set;
- socket exists at `/tmp/ppi/<uid>/<workspace_id>/worker.sock` if `XDG_RUNTIME_DIR` is not set.

## 3. Check worker status

```bash
ppi --repo "$PPI_TEST_PROJECT" worker status --json
```

Expected:

- command performs `worker.health`;
- JSON contains `status=healthy`;
- worker id matches the worker from step 2;
- no second worker process is created.

## 4. Attach second client

Open a second terminal and run:

```bash
ppi --repo "$PPI_TEST_PROJECT" worker status --json
```

Expected:

- second client reports same `worker_id`;
- no duplicate worker process is created.

## 5. Start analysis through worker

```bash
ppi --repo "$PPI_TEST_PROJECT" analyze --via-worker
```

Expected:

- command sends `analysis.start` with `mode=incremental`;
- output shows run id;
- worker state becomes `busy` during analysis and `idle` after completion;
- progress is visible through events or status polling.

## 6. Duplicate analysis start

While analysis is running, run in another terminal:

```bash
ppi --repo "$PPI_TEST_PROJECT" analyze --via-worker
```

Expected:

- no second analysis starts;
- response is success, not error;
- response includes the active run id;
- response state is exactly `already_running`.

## 7. Query through worker

After analysis has completed, run:

```bash
ppi --repo "$PPI_TEST_PROJECT" query --via-worker --metric snapshot-table-modules --format json
```

Expected:

- command sends `query.execute` with the existing CLI mapping for `--metric snapshot-table-modules`; expected worker `query_name` is exactly `snapshot/table/modules`;
- response is structured JSON;
- unknown query name returns `UNKNOWN_QUERY` in tests, including names not present in `QueryMethod` such as `snapshot/modules` and `catalog`.

## 8. Busy query behavior

While analysis is running, run:

```bash
ppi --repo "$PPI_TEST_PROJECT" query --via-worker --metric snapshot-table-modules --format json
```

Expected:

- command exits non-zero;
- structured error code is `WORKER_BUSY`.

## 9. Stale metadata recovery

Steps:

1. Start worker.
2. Kill worker process manually.
3. Keep runtime metadata/socket files if they remain.
4. Run:

```bash
ppi --repo "$PPI_TEST_PROJECT" worker status --json
```

Expected:

- stale metadata is detected;
- command does not hang;
- status is `stale` or `unavailable` with remediation message.

Then run:

```bash
ppi --repo "$PPI_TEST_PROJECT" worker start --json
```

Expected:

- new worker starts;
- runtime metadata is replaced/updated;
- health check succeeds.

## 10. Stop worker

```bash
ppi --repo "$PPI_TEST_PROJECT" worker stop --json
```

Expected:

- if idle, worker accepts shutdown;
- later status reports no healthy worker or stopped metadata;
- if busy, command exits non-zero with `WORKER_BUSY`.

## 11. FastAPI validation

```bash
ppi --repo "$PPI_TEST_PROJECT" serve
```

Expected:

- server starts or attaches worker before app startup;
- `GET /api/worker/health` returns worker health;
- `GET /api/worker/analysis/status` returns analysis status;
- `POST /api/worker/analysis/start` starts analysis or returns `already_running`.

## 12. Protocol mismatch validation

Use a test client that sends protocol version `2.0` to a `1.0` worker.

Expected:

- response is structured error;
- error code is `INCOMPATIBLE_PROTOCOL`;
- worker does not crash.
