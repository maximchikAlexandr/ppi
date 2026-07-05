"""Contract test: every required error code exists in WorkerErrorCode."""

from ppi.worker_ipc.protocol import WorkerErrorCode


def test_all_required_error_codes_exist() -> None:
    required = {
        "INVALID_REQUEST",
        "UNKNOWN_COMMAND",
        "INCOMPATIBLE_PROTOCOL",
        "WORKSPACE_MISMATCH",
        "WORKER_NOT_READY",
        "WORKER_BUSY",
        "ANALYSIS_ALREADY_RUNNING",
        "NO_ACTIVE_ANALYSIS",
        "UNKNOWN_QUERY",
        "QUERY_FAILED",
        "STORAGE_UNAVAILABLE",
        "INTERNAL_ERROR",
    }
    existing = {e.value for e in WorkerErrorCode}
    missing = required - existing
    assert not missing, f"Missing error codes: {missing}"
