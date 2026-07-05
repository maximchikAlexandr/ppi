import msgspec

from ppi.worker_ipc.protocol import (
    AnalysisState,
    WorkerCommand,
    WorkerErrorCode,
    WorkerEvent,
    WorkerEventType,
    WorkerRequest,
    WorkerResponse,
    WorkerState,
    make_error_response,
    make_success_response,
    protocol_major,
)


def test_worker_state_values() -> None:
    values = [s.value for s in WorkerState]
    assert "ready" not in values
    assert "starting" in values
    assert "idle" in values
    assert "busy" in values
    assert "stopping" in values
    assert "stopped" in values
    assert "failed" in values
    assert "stale" in values


def test_analysis_state_values() -> None:
    assert AnalysisState.not_started.value == "not_started"
    assert AnalysisState.running.value == "running"
    assert AnalysisState.completed.value == "completed"
    assert AnalysisState.failed.value == "failed"
    assert AnalysisState.cancelled.value == "cancelled"


def test_worker_command_values() -> None:
    assert WorkerCommand.WORKER_HEALTH.value == "worker.health"
    assert WorkerCommand.WORKSPACE_INFO.value == "workspace.info"
    assert WorkerCommand.ANALYSIS_STATUS.value == "analysis.status"
    assert WorkerCommand.ANALYSIS_START.value == "analysis.start"
    assert WorkerCommand.ANALYSIS_CANCEL.value == "analysis.cancel"
    assert WorkerCommand.QUERY_EXECUTE.value == "query.execute"
    assert WorkerCommand.EVENTS_SUBSCRIBE.value == "events.subscribe"
    assert WorkerCommand.WORKER_SHUTDOWN.value == "worker.shutdown"


def test_worker_event_type_values() -> None:
    assert WorkerEventType.WORKER_READY.value == "worker.ready"
    assert WorkerEventType.ANALYSIS_STARTED.value == "analysis.started"
    assert WorkerEventType.ANALYSIS_PROGRESS.value == "analysis.progress"
    assert WorkerEventType.ANALYSIS_COMPLETED.value == "analysis.completed"
    assert WorkerEventType.ANALYSIS_FAILED.value == "analysis.failed"


def test_error_code_values() -> None:
    codes = set(e.value for e in WorkerErrorCode)
    required = {
        "INVALID_REQUEST", "UNKNOWN_COMMAND", "INCOMPATIBLE_PROTOCOL",
        "WORKSPACE_MISMATCH", "WORKER_NOT_READY", "WORKER_BUSY",
        "ANALYSIS_ALREADY_RUNNING", "NO_ACTIVE_ANALYSIS", "UNKNOWN_QUERY",
        "QUERY_FAILED", "STORAGE_UNAVAILABLE", "INTERNAL_ERROR",
    }
    assert codes == required


def test_worker_request_roundtrip() -> None:
    req = WorkerRequest(
        request_id="req-1",
        protocol_version="1.0",
        workspace_id="ws-1",
        command="worker.health",
        payload={},
    )
    encoded = msgspec.msgpack.encode(req)
    decoded = msgspec.msgpack.decode(encoded, type=WorkerRequest)
    assert decoded.request_id == "req-1"
    assert decoded.protocol_version == "1.0"
    assert decoded.command == "worker.health"


def test_worker_response_roundtrip() -> None:
    resp = make_success_response("req-1", {"state": "idle"})
    encoded = msgspec.msgpack.encode(resp)
    decoded = msgspec.msgpack.decode(encoded, type=WorkerResponse)
    assert decoded.ok is True
    assert decoded.result == {"state": "idle"}


def test_error_response_roundtrip() -> None:
    resp = make_error_response("req-1", "WORKER_BUSY", "Worker is busy")
    encoded = msgspec.msgpack.encode(resp)
    decoded = msgspec.msgpack.decode(encoded, type=WorkerResponse)
    assert decoded.ok is False
    assert decoded.error is not None
    assert decoded.error.code == "WORKER_BUSY"


def test_worker_event_roundtrip() -> None:
    event = WorkerEvent(
        event_id="evt-1",
        workspace_id="ws-1",
        worker_id="w-1",
        event_type="analysis.progress",
        created_at="2026-07-04T12:00:00Z",
        payload={"run_id": "run-1", "progress_percent": 50.0},
    )
    encoded = msgspec.msgpack.encode(event)
    decoded = msgspec.msgpack.decode(encoded, type=WorkerEvent)
    assert decoded.event_type == "analysis.progress"
    assert decoded.payload["progress_percent"] == 50.0



def test_protocol_major_parsing() -> None:
    assert protocol_major("1.0") == 1
    assert protocol_major("1.5") == 1
    assert protocol_major("2.0") == 2


def test_incompatible_major_version() -> None:
    req = WorkerRequest(
        request_id="req-1",
        protocol_version="2.0",
        workspace_id="ws-1",
        command="worker.health",
        payload={},
    )
    from ppi.worker_ipc.constants import PROTOCOL_MAJOR
    from ppi.worker_ipc.protocol import protocol_major

    assert protocol_major(req.protocol_version) != PROTOCOL_MAJOR
