# Tasks: Worker IPC Runtime Boundary

**Feature**: `009-worker-ipc-runtime-boundary`  
**Spec**: `specs/009-worker-ipc-runtime-boundary/spec.md`  
**Plan**: `specs/009-worker-ipc-runtime-boundary/plan.md`  
**Status**: Ready for implementation
**Reviewed**: 2026-07-05 ambiguity pass for weaker implementing model

## Implementation rules for the weaker implementing model

Follow these decisions exactly. Do not replace them with alternatives.

1. New Python package is exactly `src/ppi/worker_ipc/`.
2. Only Unix domain socket transport is implemented in this feature.
3. Message encoding is `msgspec` MessagePack.
4. Framing is exactly 4-byte unsigned big-endian payload length + payload bytes.
5. Maximum frame size is exactly `16_777_216` bytes.
6. Protocol version is exactly `1.0`.
7. Runtime paths are exactly those in `contracts/runtime-files.md`.
8. Workspace registry is JSON at `~/.local/share/ppi/workspaces.json`, with test override `PPI_WORKSPACE_REGISTRY`.
9. Workspace id is derived from `ppi.runtime.paths.project_id_from_repo(repo)`.
10. Existing CLI global `--repo` stays required; do not add a new `--workspace` option in this feature.
11. Duplicate `analysis.start` returns success with `state=already_running`; do not return an error for this normal case.
12. `query.execute` while analysis is running returns `WORKER_BUSY`.
13. `worker.shutdown` while analysis is running returns `WORKER_BUSY`.
14. Do not implement TCP, WSS, public webserver-to-local-worker, remote Git import, plugin refactor, or event replay.
15. Do not add a `ready` worker state. `worker.ready` is only an event emitted with payload `state=idle`.
16. Do not invent query names; derive allowed query names from `ppi.query.dispatch.QueryMethod` and assert they match `contracts/protocol.md`.
17. Normalize every `query.execute` result to `{columns, rows, row_count, truncated}` before IPC encoding.

## User stories used for task grouping

- **US1**: CLI can start, check, attach to, and stop one workspace worker.
- **US2**: Startup discovery prevents duplicate workers and recovers stale metadata.
- **US3**: Worker handles analysis status/start/cancel and live events.
- **US4**: Worker executes whitelisted read-only queries.
- **US5**: FastAPI and IDE-facing flows can use the worker boundary.

## Phase 1: Setup

- [X] T001 Create package marker for the new IPC package in `src/ppi/worker_ipc/__init__.py`
- [X] T002 Create test package marker in `tests/worker_ipc/__init__.py`
- [X] T003 Add worker IPC constants exactly as listed in the plan to `src/ppi/worker_ipc/constants.py`
- [X] T004 Add `if __name__ == "__main__": cli()` module execution support to `src/ppi/cli/main.py`
- [X] T005 Add worker IPC quick import smoke test for package import and constants in `tests/worker_ipc/test_imports.py`
- [X] T006 Update CLI help text to mention worker-backed mode in `src/ppi/cli/main.py`

## Phase 2: Foundational protocol, framing, paths, registry, and metadata

- [X] T007 [P] Define `WorkerState`, `AnalysisState`, `WorkerCommand`, `WorkerEventType`, and `WorkerErrorCode` enums in `src/ppi/worker_ipc/protocol.py`
- [X] T008 [P] Define `WorkerError`, `WorkerRequest`, `WorkerResponse`, `WorkerEvent`, `WorkspaceInfo`, and `AnalysisStatus` msgspec structs in `src/ppi/worker_ipc/protocol.py`
- [X] T009 [P] Add `make_success_response`, `make_error_response`, and `protocol_major` helpers in `src/ppi/worker_ipc/protocol.py`
- [X] T010 [P] Add protocol contract tests for enum values and struct round-trip encoding in `tests/worker_ipc/test_protocol.py`, including assertion that `ready` is not a `WorkerState` value
- [X] T011 [P] Add protocol tests for incompatible major version parsing in `tests/worker_ipc/test_protocol.py`
- [X] T012 Implement `FrameTooLargeError`, `IncompleteFrameError`, `read_frame`, and `write_frame` in `src/ppi/worker_ipc/framing.py`
- [X] T013 Add framing tests for one frame encode/decode in `tests/worker_ipc/test_framing.py`
- [X] T014 Add framing tests for multiple frames on one stream in `tests/worker_ipc/test_framing.py`
- [X] T015 Add framing tests for frame size > 16 MiB and incomplete payload in `tests/worker_ipc/test_framing.py`
- [X] T016 Implement `Endpoint` dataclass and `parse_endpoint` for `unix://` URIs in `src/ppi/worker_ipc/endpoint.py`
- [X] T017 Add endpoint parser tests for valid Unix endpoint and unsupported TCP/WSS diagnostics in `tests/worker_ipc/test_endpoint.py`
- [X] T018 Implement `runtime_root`, `runtime_dir`, `socket_path`, `metadata_path`, `startup_lock_path`, and `endpoint_for_workspace` in `src/ppi/worker_ipc/runtime_paths.py`
- [X] T019 Add runtime path tests for `XDG_RUNTIME_DIR` and `/tmp/ppi/<uid>` fallback in `tests/worker_ipc/test_runtime_paths.py`
- [X] T020 Implement `WorkspaceRegistration` msgspec struct and JSON registry path helper in `src/ppi/worker_ipc/registry.py`
- [X] T021 Implement `load_registry`, `save_registry`, `register_or_update_from_repo`, `get_workspace`, `resolve_workspace_from_repo`, and `list_workspaces` in `src/ppi/worker_ipc/registry.py`
- [X] T022 Add registry tests using `PPI_WORKSPACE_REGISTRY` temp file in `tests/worker_ipc/test_registry.py`
- [X] T023 Implement `RuntimeMetadata` msgspec struct and JSON read/write helpers in `src/ppi/worker_ipc/runtime_metadata.py`
- [X] T024 Implement `mark_stale`, `remove_metadata`, and corrupted metadata handling in `src/ppi/worker_ipc/runtime_metadata.py`
- [X] T025 Add runtime metadata tests for read/write, corrupted JSON, missing file, and stale marking in `tests/worker_ipc/test_runtime_metadata.py`
- [X] T026 Implement `worker_startup_lock(path)` by reusing or wrapping `ppi.runtime.lock.write_lock` in `src/ppi/worker_ipc/locks.py`
- [X] T027 Add startup lock tests for acquire/release and stale pid cleanup in `tests/worker_ipc/test_locks.py`
- [X] T028 Implement `UnixClientTransport` using `asyncio.open_unix_connection` and shared framing in `src/ppi/worker_ipc/unix_transport.py`
- [X] T029 Implement `UnixServerTransport` using `asyncio.start_unix_server` and shared framing in `src/ppi/worker_ipc/unix_transport.py`
- [X] T030 Add Unix transport integration test for client/server frame exchange in `tests/worker_ipc/test_unix_transport.py`
- [X] T031 Implement `WorkerClient.request()` with request id generation, MessagePack encoding, response decoding, and command timeout in `src/ppi/worker_ipc/client.py`
- [X] T032 Implement typed `WorkerClient.health`, `workspace_info`, `analysis_status`, `analysis_start`, `analysis_cancel`, `query_execute`, `events_subscribe`, and `shutdown` methods in `src/ppi/worker_ipc/client.py`
- [X] T033 Add client tests using a fake Unix server for success response and structured error response in `tests/worker_ipc/test_client.py`
- [X] T034 Implement `EventHub` with per-client bounded async queues in `src/ppi/worker_ipc/events.py`
- [X] T035 Implement slow subscriber disconnect behavior in `src/ppi/worker_ipc/events.py`
- [X] T036 Add EventHub tests for broadcast to two subscribers and slow subscriber removal in `tests/worker_ipc/test_events.py`
- [X] T037 Create `WorkerServer` connection loop that decodes requests and sends responses in `src/ppi/worker_ipc/server.py`
- [X] T038 Add server tests for invalid request, unknown command, workspace mismatch, and protocol mismatch in `tests/worker_ipc/test_server_protocol_errors.py`

## Phase 3: US1 - CLI can start, check, attach to, and stop one workspace worker

**Independent test**: `ppi --repo <repo> worker start --json`, `worker status --json`, and `worker stop --json` work on a temp repository; a second status call reports the same `worker_id`.

- [X] T039 [US1] Implement `WorkerRuntime` constructor with workspace registration, worker id, state, started_at, and initial `AnalysisStatus(not_started)` in `src/ppi/worker_ipc/worker_runtime.py`
- [X] T040 [US1] Implement `worker.health`, `workspace.info`, and `analysis.status` handlers in `src/ppi/worker_ipc/worker_runtime.py`
- [X] T041 [US1] Implement `worker.shutdown` handler that succeeds only when state is `idle` and returns `WORKER_BUSY` when state is `busy` in `src/ppi/worker_ipc/worker_runtime.py`
- [X] T042 [US1] Implement runtime metadata write on startup, heartbeat update every 5 seconds, and stopped metadata update on shutdown in `src/ppi/worker_ipc/worker_runtime.py`
- [X] T043 [US1] Add worker runtime tests for health/workspace/status/shutdown handlers in `tests/worker_ipc/test_worker_runtime_basic.py`
- [X] T044 [US1] Implement `run_worker_foreground(ctx)` to start Unix server and wait for shutdown in `src/ppi/worker_ipc/cli_handlers.py`
- [X] T045 [US1] Implement `Supervisor.spawn_worker()` using `subprocess.Popen([sys.executable, "-m", "ppi.cli.main", ... "worker", "run"])` in `src/ppi/worker_ipc/supervisor.py`
- [X] T046 [US1] Implement `Supervisor.wait_until_healthy()` with 10 second timeout in `src/ppi/worker_ipc/supervisor.py`
- [X] T047 [US1] Implement `WorkerGateway.get_client(start_if_missing=False)` discovery without spawning in `src/ppi/worker_ipc/gateway.py`
- [X] T048 [US1] Implement `WorkerGateway.get_client(start_if_missing=True)` discovery plus startup lock plus supervisor spawn in `src/ppi/worker_ipc/gateway.py`
- [X] T049 [US1] Add gateway tests for attach to healthy metadata and no-start unavailable result in `tests/worker_ipc/test_gateway_discovery.py`
- [X] T050 [US1] Add `worker` click command group to `src/ppi/cli/main.py`
- [X] T051 [US1] Add `worker run` hidden command that calls `run_worker_foreground(ctx)` in `src/ppi/cli/main.py`
- [X] T052 [US1] Add `worker start --json` command that calls gateway with startup allowed in `src/ppi/cli/main.py`
- [X] T053 [US1] Add `worker status --json` command that calls gateway with startup disabled in `src/ppi/cli/main.py`
- [X] T054 [US1] Add `worker stop --json` command that sends `worker.shutdown` and handles no-worker as successful no-op in `src/ppi/cli/main.py`
- [X] T055 [US1] Add CLI unit tests for worker start/status/stop output shape with monkeypatched gateway in `tests/worker_ipc/test_cli_worker_commands.py`
- [X] T056 [US1] Add integration test that starts real foreground worker process and calls health through WorkerClient in `tests/worker_ipc/test_integration_worker_lifecycle.py`
- [X] T057 [US1] Add integration test that `worker stop` stops an idle worker and later status is not healthy in `tests/worker_ipc/test_integration_worker_lifecycle.py`

## Phase 4: US2 - Startup discovery prevents duplicate workers and recovers stale metadata

**Independent test**: two simultaneous gateway startup attempts for the same repo produce one worker id; stale metadata from a dead pid is detected before attach.

- [X] T058 [US2] Implement health-check validation of workspace id, protocol major version, and worker state in `src/ppi/worker_ipc/gateway.py`
- [X] T059 [US2] Implement stale metadata overwrite only after failed health check in `src/ppi/worker_ipc/gateway.py`
- [X] T060 [US2] Implement startup-lock re-check inside the lock before spawning in `src/ppi/worker_ipc/gateway.py`
- [X] T061 [US2] Implement bounded retry for lock loser to re-run discovery after another process starts worker in `src/ppi/worker_ipc/gateway.py`
- [X] T062 [US2] Add gateway test for metadata workspace mismatch in `tests/worker_ipc/test_gateway_stale.py`
- [X] T063 [US2] Add gateway test for incompatible protocol major version in `tests/worker_ipc/test_gateway_stale.py`
- [X] T064 [US2] Add gateway test for stale socket/metadata when Unix connect fails in `tests/worker_ipc/test_gateway_stale.py`
- [X] T065 [US2] Add gateway test that startup lock loser attaches to worker spawned by lock winner in `tests/worker_ipc/test_gateway_race.py`
- [X] T066 [US2] Add integration test with two concurrent `worker start` calls that returns one worker id in `tests/worker_ipc/test_integration_duplicate_start.py`
- [X] T067 [US2] Add integration test that killing the worker and running status reports stale/unavailable without hanging in `tests/worker_ipc/test_integration_stale_metadata.py`
- [X] T068 [US2] Add integration test that `worker start` after stale metadata starts a new worker id in `tests/worker_ipc/test_integration_stale_metadata.py`
- [X] T069 [US2] Ensure stale socket file is unlinked only after failed health check in `src/ppi/worker_ipc/gateway.py`
- [X] T070 [US2] Add diagnostic result object for `healthy`, `stale`, `unavailable`, `workspace_mismatch`, and `incompatible_protocol` statuses in `src/ppi/worker_ipc/gateway.py`
- [X] T071 [US2] Update `worker status --json` to output the diagnostic status object in `src/ppi/cli/main.py`
- [X] T072 [US2] Add CLI test for `worker status --json` stale output in `tests/worker_ipc/test_cli_worker_commands.py`
- [X] T073 [US2] Add `doctor --recover-stale` worker metadata cleanup note without changing existing store cleanup behavior in `src/ppi/cli/main.py`

## Phase 5: US3 - Worker handles analysis status/start/cancel and live events

**Independent test**: starting analysis through worker changes state to `busy`, emits started/progress/completed or failed events, and duplicate start returns `already_running` with the same run id.

- [X] T074 [US3] Extract reusable analysis execution config from existing `analyze` command into `src/ppi/worker_ipc/analysis_service.py`
- [X] T075 [US3] Implement `AnalysisService.run_incremental()` by calling existing history walk and StoreWriter logic in `src/ppi/worker_ipc/analysis_service.py`
- [X] T076 [US3] Implement `AnalysisService.run_full()` by using the existing rebuild/clear-project-data behavior in `src/ppi/worker_ipc/analysis_service.py`
- [X] T077 [US3] Implement progress callback support that emits processed commit count and percent in `src/ppi/worker_ipc/analysis_service.py`
- [X] T078 [US3] Implement cooperative cancellation flag checked between commit batches in `src/ppi/worker_ipc/analysis_service.py`
- [X] T079 [US3] Add analysis service unit tests with fake batches for completed, failed, and cancelled runs in `tests/worker_ipc/test_analysis_service.py`
- [X] T080 [US3] Implement `analysis.start` handler to create run id, set state `busy`, start one background task, and return `running` in `src/ppi/worker_ipc/worker_runtime.py`
- [X] T081 [US3] Implement duplicate `analysis.start` handler to return `ok=true`, `accepted=true`, same run id, and `state=already_running` in `src/ppi/worker_ipc/worker_runtime.py`
- [X] T082 [US3] Implement `analysis.cancel` handler to set cancellation flag or return `accepted=false` when no active run exists in `src/ppi/worker_ipc/worker_runtime.py`
- [X] T083 [US3] Implement analysis event emission for `analysis.started`, `analysis.progress`, `analysis.completed`, `analysis.cancelled`, and `analysis.failed` in `src/ppi/worker_ipc/worker_runtime.py`
- [X] T084 [US3] Implement worker state events `worker.ready`, `worker.state_changed`, and `worker.failed` in `src/ppi/worker_ipc/worker_runtime.py`; emit `worker.ready` only when state becomes `idle` after startup
- [X] T085 [US3] Add worker runtime tests for `analysis.start`, duplicate start, status during run, and cancel without active run in `tests/worker_ipc/test_worker_runtime_analysis.py`
- [X] T086 [US3] Add event subscription test that subscribed client receives `analysis.started` and `analysis.progress` in `tests/worker_ipc/test_worker_runtime_events.py`
- [X] T087 [US3] Add `--via-worker` option to existing `analyze` command in `src/ppi/cli/main.py`
- [X] T088 [US3] Implement worker-backed analyze path that maps `--rebuild` to `mode=full` and default to `mode=incremental` in `src/ppi/cli/main.py`
- [X] T089 [US3] Implement worker-backed analyze progress display by subscribing to events or polling `analysis.status` in `src/ppi/cli/main.py`
- [X] T090 [US3] Add CLI tests for `analyze --via-worker` start and `already_running` output in `tests/worker_ipc/test_cli_analyze_via_worker.py`
- [X] T091 [US3] Add integration test for duplicate `analysis.start` over two clients returning same run id and `already_running` in `tests/worker_ipc/test_integration_analysis.py`
- [X] T092 [US3] Add integration test that client disconnect during analysis does not stop worker in `tests/worker_ipc/test_integration_analysis.py`
- [X] T093 [US3] Add integration test that `worker stop` during running analysis returns `WORKER_BUSY` in `tests/worker_ipc/test_integration_analysis.py`
- [X] T094 [US3] Update quickstart analysis examples after implementation details are confirmed in `specs/009-worker-ipc-runtime-boundary/quickstart.md`

## Phase 6: US4 - Worker executes whitelisted read-only queries

**Independent test**: after analysis data exists, `query.execute` with `snapshot/table/modules` succeeds through worker; unknown query, including legacy or invented names such as `snapshot/modules` and `catalog`, returns `UNKNOWN_QUERY`; query during active analysis returns `WORKER_BUSY`.

- [X] T095 [US4] Implement allowed query-name set from `ppi.query.dispatch.QueryMethod` values in `src/ppi/worker_ipc/query_service.py` and add a failing-fast assertion/test that this set matches `contracts/protocol.md`
- [X] T096 [US4] Implement `QueryService.execute()` that opens `StoreReader` read-only and calls `ppi.query.dispatch.dispatch` in `src/ppi/worker_ipc/query_service.py`
- [X] T097 [US4] Implement result normalization for dict/list/Pydantic `model_dump(mode="json")` values in `src/ppi/worker_ipc/query_service.py`
- [X] T098 [US4] Implement `query.execute` handler that returns `WORKER_BUSY` while runtime state is `busy` in `src/ppi/worker_ipc/worker_runtime.py`
- [X] T099 [US4] Implement deterministic `query.execute` result normalization with `columns`, `rows`, `row_count`, and `truncated`: dict/object => one row, list => rows list, scalar => `{"value": scalar}`, optional `limit` applied after normalization in `src/ppi/worker_ipc/worker_runtime.py`
- [X] T100 [US4] Add query service tests for allowed query, unknown query including legacy/invented names such as `snapshot/modules` and `catalog`, store missing, list/dict/scalar/Pydantic normalization, and limit truncation in `tests/worker_ipc/test_query_service.py`
- [X] T101 [US4] Add worker runtime test for `query.execute` returning `WORKER_BUSY` during running analysis in `tests/worker_ipc/test_worker_runtime_query.py`
- [X] T102 [US4] Add `--via-worker` option to existing `query` command in `src/ppi/cli/main.py`
- [X] T103 [US4] Implement worker-backed query path using existing `_cli_metric_to_method` mapping in `src/ppi/cli/main.py`
- [X] T104 [US4] Add CLI tests for `query --via-worker --metric snapshot-table-modules --format json` using the existing `_cli_metric_to_method` mapping in `tests/worker_ipc/test_cli_query_via_worker.py`
- [X] T105 [US4] Add integration test for worker-backed `snapshot/table/modules` query after a prepared test store exists in `tests/worker_ipc/test_integration_query.py`

## Phase 7: US5 - FastAPI and IDE-facing flows can use the worker boundary

**Independent test**: `ppi serve` starts or attaches a worker, and `/api/worker/*` endpoints proxy worker commands without writing storage directly.

- [X] T106 [US5] Implement FastAPI router for `/api/worker/health`, `/api/worker/workspace`, and `/api/worker/analysis/status` in `src/ppi/server/worker_api.py`
- [X] T107 [US5] Implement FastAPI router handlers for `/api/worker/analysis/start` and `/api/worker/analysis/cancel` in `src/ppi/server/worker_api.py`
- [X] T108 [US5] Implement FastAPI router handler for `/api/worker/query` in `src/ppi/server/worker_api.py`
- [X] T109 [US5] Implement worker error to HTTP JSON conversion preserving `code`, `message`, `details`, and `recoverable` in `src/ppi/server/worker_api.py`
- [X] T110 [US5] Modify `create_app` to accept optional worker gateway/client and include `worker_api.router` when provided in `src/ppi/server/app.py`
- [X] T111 [US5] Modify `serve` CLI command to start or attach worker before app creation and pass the worker dependency to `create_app` in `src/ppi/cli/main.py`
- [X] T112 [US5] Add FastAPI tests for `/api/worker/health` and `/api/worker/analysis/status` with fake WorkerClient in `tests/worker_ipc/test_fastapi_worker_api.py`
- [X] T113 [US5] Add FastAPI tests for structured worker error to HTTP JSON conversion in `tests/worker_ipc/test_fastapi_worker_api.py`
- [X] T114 [US5] Add FastAPI test that `/api/worker/analysis/start` returns `already_running` unchanged when worker returns it in `tests/worker_ipc/test_fastapi_worker_api.py`
- [X] T115 [US5] Add serve CLI test that gateway is called before `create_app` in `tests/worker_ipc/test_cli_serve_worker.py`
- [X] T116 [US5] Add IDE migration note with exact supported CLI commands in `vscode-extension/README.md`
- [X] T117 [US5] Add Python-side IDE bridge contract note with worker command mapping in `src/ppi/worker_ipc/ide_contract.py`
- [X] T118 [US5] Add test that `ide_contract.py` exports the documented command list in `tests/worker_ipc/test_ide_contract.py`
- [X] T119 [US5] Update README worker IPC section and mark old `ppi rpc` as legacy bridge for IDE in `README.md`

## Phase 8: Polish, validation, and guardrails

- [X] T120 Add architecture guardrail test that `src/ppi/worker_ipc/protocol.py` imports no FastAPI/server modules in `tests/worker_ipc/test_architecture_boundaries.py`
- [X] T121 Add architecture guardrail test that `src/ppi/server/worker_api.py` uses WorkerClient/Gateway and does not import StoreWriter in `tests/worker_ipc/test_architecture_boundaries.py`
- [X] T122 Add contract test that every required command in `contracts/protocol.md` is present in `WorkerRuntime` dispatch table in `tests/worker_ipc/test_contract_command_coverage.py`
- [X] T123 Add contract test that every required event type in `contracts/protocol.md` exists in `WorkerEventType` and that `worker.ready` payload state is `idle` in `tests/worker_ipc/test_contract_event_coverage.py`
- [X] T124 Add contract test that every required error code in `contracts/protocol.md` exists in `WorkerErrorCode` in `tests/worker_ipc/test_contract_error_coverage.py`
- [X] T125 Update generated OpenAPI output expectation for `/api/worker/*` endpoints in `tests/worker_ipc/test_openapi_worker_endpoints.py`
- [X] T126 Update manual validation commands after final CLI behavior is implemented in `specs/009-worker-ipc-runtime-boundary/quickstart.md`
- [X] T127 Update decision log with implementation deviations if any deviation was required in `.speckit-chat/decision-log.md`
- [X] T128 Run full test suite command and record passing command/output summary in `specs/009-worker-ipc-runtime-boundary/checklists/implementation-validation.md`
- [X] T129 Add contract test that allowed query names in `contracts/protocol.md` exactly match `ppi.query.dispatch.QueryMethod` values in `tests/worker_ipc/test_contract_query_coverage.py`

## Dependencies

### Hard ordering

- Phase 1 before all other phases.
- Phase 2 before US1-US5.
- US1 before US2 because duplicate startup tests require working start/status/stop.
- US1 before US3 because analysis runs inside the worker runtime.
- US3 before US4 because query-busy behavior depends on worker busy state.
- US1 before US5 because FastAPI endpoints need a working WorkerClient/Gateway.
- Phase 8 last.

### Parallel work allowed

- T007-T011 can run in parallel with T012-T019 after T003.
- T020-T027 can run in parallel with T028-T038 after protocol structs exist.
- T062-T068 can be written in parallel after T058-T061 define expected behavior.
- T095-T100 can run in parallel with T102-T104 after WorkerClient exists.
- T106-T109 can run in parallel with T116-T118 after WorkerClient method names are stable.

## Parallel execution examples

```text
Agent A: T007-T011 protocol and protocol tests
Agent B: T012-T015 framing and framing tests
Agent C: T018-T025 runtime paths, registry, metadata, and tests
```

```text
Agent A: T080-T086 worker analysis handlers and tests
Agent B: T087-T090 CLI analyze --via-worker and tests
Agent C: T091-T093 integration tests
```

## MVP scope

The implementation is MVP-complete after these task ranges pass:

```text
T001-T057  worker lifecycle through CLI
T058-T073  duplicate startup and stale recovery
T074-T094  worker-backed analysis and events
T095-T105 plus T129  worker-backed query
T106-T115  FastAPI worker endpoints
T120-T129  guardrails and validation
```

T116-T119 are documentation/contract tasks for IDE and README parity. Complete them before merging; they do not block Python IPC functionality.

## Story-level test criteria

- **US1**: start/status/stop CLI commands work and a second client sees the same worker id.
- **US2**: duplicate startup race creates one worker and stale metadata does not hang or attach to a dead worker.
- **US3**: analysis start/status/cancel and events work; duplicate start returns `already_running` success.
- **US4**: whitelisted query works after analysis data exists; unknown/busy query returns structured error.
- **US5**: FastAPI `/api/worker/*` endpoints proxy worker commands and preserve structured errors.

## Final validation commands

Run these from the repository root after implementation:

```bash
uv run pytest tests/worker_ipc -q
uv run pytest -q
uv run ruff check src tests
uv run ppi --repo /abs/path/to/test-project worker start --json
uv run ppi --repo /abs/path/to/test-project worker status --json
uv run ppi --repo /abs/path/to/test-project worker stop --json
```

If `uv run pytest -q` fails outside `tests/worker_ipc` because of pre-existing unrelated tests, record that explicitly in `specs/009-worker-ipc-runtime-boundary/checklists/implementation-validation.md` and still keep all `tests/worker_ipc` tests passing.
