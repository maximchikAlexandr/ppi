from __future__ import annotations

from typing import NoReturn

from fastapi import APIRouter, HTTPException, Request

from ppi.worker_ipc.client import WorkerClientError, WorkerClientProtocol
from ppi.worker_ipc.protocol import AnalysisRequestMode, AnalysisStartRequest, WorkerErrorCode

router = APIRouter(prefix="/api/worker", tags=["worker"])


def _get_client(request: Request) -> WorkerClientProtocol:
    app = request.app
    client: WorkerClientProtocol | None = getattr(app.state, "worker_client", None)
    if client is None:
        raise HTTPException(status_code=503, detail="Worker not available")
    return client


def _error_to_http(exc: WorkerClientError) -> NoReturn:
    err = exc.error
    status_map: dict[str, int] = {
        WorkerErrorCode.INVALID_REQUEST: 400,
        WorkerErrorCode.UNKNOWN_COMMAND: 404,
        WorkerErrorCode.WORKSPACE_MISMATCH: 409,
        WorkerErrorCode.WORKER_BUSY: 409,
        WorkerErrorCode.ANALYSIS_ALREADY_RUNNING: 409,
        WorkerErrorCode.UNKNOWN_QUERY: 404,
        WorkerErrorCode.QUERY_FAILED: 500,
        WorkerErrorCode.STORAGE_UNAVAILABLE: 503,
        WorkerErrorCode.INTERNAL_ERROR: 500,
    }
    status = status_map.get(err.code, 500)
    raise HTTPException(
        status_code=status,
        detail={
            "code": err.code,
            "message": err.message,
            "details": err.details,
            "recoverable": err.recoverable,
        },
    )


@router.get("/health")
async def health(request: Request) -> dict:
    client = _get_client(request)
    try:
        return await client.health()
    except WorkerClientError as exc:
        raise _error_to_http(exc)


@router.get("/workspace")
async def workspace(request: Request) -> dict:
    client = _get_client(request)
    try:
        return await client.workspace_info()
    except WorkerClientError as exc:
        raise _error_to_http(exc)


@router.get("/analysis/status")
async def analysis_status(request: Request) -> dict:
    client = _get_client(request)
    try:
        return await client.analysis_status()
    except WorkerClientError as exc:
        raise _error_to_http(exc)


@router.post("/analysis/start")
async def analysis_start(request: Request, body: dict | None = None) -> dict:
    client = _get_client(request)
    payload = body or {}
    try:
        # HTTP callers may omit a branch; the worker is the explicit adapter
        # context and resolves it before analysis. CLI requests are concrete.
        return await client.analysis_start(
            AnalysisStartRequest(
                mode=AnalysisRequestMode(payload.get("mode", "incremental")),
                reason=payload.get("reason", "api"),
                branch=payload.get("branch"),
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except WorkerClientError as exc:
        raise _error_to_http(exc)


@router.post("/analysis/cancel")
async def analysis_cancel(request: Request, body: dict | None = None) -> dict:
    client = _get_client(request)
    run_id = (body or {}).get("run_id")
    reason = (body or {}).get("reason", "api")
    try:
        return await client.analysis_cancel(run_id=run_id, reason=reason)
    except WorkerClientError as exc:
        raise _error_to_http(exc)


@router.post("/query")
async def query_execute(request: Request, body: dict) -> dict:
    client = _get_client(request)
    query_name = body.get("query_name", "")
    parameters = body.get("parameters", {})
    limit = body.get("limit")
    try:
        return await client.query_execute(query_name=query_name, parameters=parameters, limit=limit)
    except WorkerClientError as exc:
        _error_to_http(exc)
