from __future__ import annotations

from enum import StrEnum
from typing import Any

import msgspec


class WorkerState(StrEnum):
    starting = "starting"
    idle = "idle"
    busy = "busy"
    stopping = "stopping"
    stopped = "stopped"
    failed = "failed"
    stale = "stale"


class AnalysisState(StrEnum):
    not_started = "not_started"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class WorkerCommand(StrEnum):
    WORKER_HEALTH = "worker.health"
    WORKSPACE_INFO = "workspace.info"
    ANALYSIS_STATUS = "analysis.status"
    ANALYSIS_START = "analysis.start"
    ANALYSIS_CANCEL = "analysis.cancel"
    QUERY_EXECUTE = "query.execute"
    EVENTS_SUBSCRIBE = "events.subscribe"
    WORKER_SHUTDOWN = "worker.shutdown"


class WorkerEventType(StrEnum):
    WORKER_READY = "worker.ready"
    WORKER_STATE_CHANGED = "worker.state_changed"
    WORKER_WARNING = "worker.warning"
    WORKER_FAILED = "worker.failed"
    ANALYSIS_STARTED = "analysis.started"
    ANALYSIS_PROGRESS = "analysis.progress"
    ANALYSIS_WARNING = "analysis.warning"
    ANALYSIS_COMPLETED = "analysis.completed"
    ANALYSIS_CANCELLED = "analysis.cancelled"
    ANALYSIS_FAILED = "analysis.failed"


class WorkerErrorCode(StrEnum):
    INVALID_REQUEST = "INVALID_REQUEST"
    UNKNOWN_COMMAND = "UNKNOWN_COMMAND"
    INCOMPATIBLE_PROTOCOL = "INCOMPATIBLE_PROTOCOL"
    WORKSPACE_MISMATCH = "WORKSPACE_MISMATCH"
    WORKER_NOT_READY = "WORKER_NOT_READY"
    WORKER_BUSY = "WORKER_BUSY"
    ANALYSIS_ALREADY_RUNNING = "ANALYSIS_ALREADY_RUNNING"
    NO_ACTIVE_ANALYSIS = "NO_ACTIVE_ANALYSIS"
    UNKNOWN_QUERY = "UNKNOWN_QUERY"
    QUERY_FAILED = "QUERY_FAILED"
    STORAGE_UNAVAILABLE = "STORAGE_UNAVAILABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class WorkerError(msgspec.Struct):
    code: str
    message: str
    details: dict[str, Any] = msgspec.field(default_factory=dict)


class WorkerRequest(msgspec.Struct):
    request_id: str
    protocol_version: str
    workspace_id: str
    command: str
    payload: dict[str, Any]


class WorkerResponse(msgspec.Struct):
    request_id: str
    ok: bool
    result: dict[str, Any] | None = None
    error: WorkerError | None = None


class WorkerEvent(msgspec.Struct):
    event_id: str
    workspace_id: str
    worker_id: str
    event_type: str
    created_at: str
    payload: dict[str, Any]




def make_success_response(request_id: str, result: dict[str, Any] | None = None) -> WorkerResponse:
    return WorkerResponse(request_id=request_id, ok=True, result=result or {})


def make_error_response(
    request_id: str,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> WorkerResponse:
    return WorkerResponse(
        request_id=request_id,
        ok=False,
        error=WorkerError(code=code, message=message, details=details or {}),
    )


def protocol_major(version: str) -> int:
    try:
        parts = version.split(".")
        return int(parts[0])
    except (ValueError, IndexError):
        return 0
