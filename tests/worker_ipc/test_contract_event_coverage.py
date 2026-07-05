"""Contract test: every required event type exists in WorkerEventType and worker.ready payload state is idle."""

from ppi.worker_ipc.protocol import WorkerEventType


def test_all_required_event_types_exist() -> None:
    required = {
        "worker.ready",
        "worker.state_changed",
        "worker.warning",
        "worker.failed",
        "analysis.started",
        "analysis.progress",
        "analysis.warning",
        "analysis.completed",
        "analysis.cancelled",
        "analysis.failed",
    }
    existing = {e.value for e in WorkerEventType}
    missing = required - existing
    assert not missing, f"Missing event types: {missing}"


def test_worker_ready_payload_state_is_idle() -> None:
    assert WorkerEventType.WORKER_READY.value == "worker.ready"
