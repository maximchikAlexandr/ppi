from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

import msgspec

from ppi.worker_ipc.constants import PROTOCOL_MAJOR
from ppi.worker_ipc.framing import read_frame, write_frame
from ppi.worker_ipc.protocol import (
    WorkerErrorCode,
    WorkerRequest,
    WorkerResponse,
    make_error_response,
    make_success_response,
    protocol_major,
)
from ppi.runtime.log import get_logger

log = get_logger("ppi.worker_ipc.server")

RECOVERABLE_CODES = frozenset({
    WorkerErrorCode.WORKER_BUSY,
    WorkerErrorCode.STORAGE_UNAVAILABLE,
})


def _is_recoverable(code: str) -> bool:
    return code in RECOVERABLE_CODES


class WorkerServer:
    def __init__(
        self,
        socket_path: str,
        workspace_id: str,
    ) -> None:
        self._socket_path = socket_path
        self._workspace_id = workspace_id
        self._server: asyncio.AbstractServer | None = None
        self._handle_request: (
            Callable[[WorkerRequest], Awaitable[dict[str, Any]]] | None
        ) = None
        self._stream_request: (
            Callable[[WorkerRequest, asyncio.StreamWriter, asyncio.StreamReader], Awaitable[None]] | None
        ) = None

    def set_handle_request(
        self,
        handler: Callable[[WorkerRequest], Awaitable[dict[str, Any]]],
    ) -> None:
        self._handle_request = handler

    def set_stream_request(
        self,
        handler: Callable[[WorkerRequest, asyncio.StreamWriter, asyncio.StreamReader], Awaitable[None]],
    ) -> None:
        self._stream_request = handler

    async def start(self, *, force: bool = True) -> None:
        """Start the server.

        ``force`` defaults to True because the worker process is the
        legitimate owner of the socket at this point (spawned by the
        gateway after startup lock acquisition). Set ``force=False``
        to refuse to unlink an existing socket.
        """
        path = Path(self._socket_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if not force:
                raise FileExistsError(
                    f"Socket {path} already exists; pass force=True to unlink stale"
                )
            path.unlink()
        self._server = await asyncio.start_unix_server(self._on_connected, path=self._socket_path)

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def _on_connected(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        try:
            raw = await read_frame(reader)
        except Exception:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            return
        try:
            req = msgspec.msgpack.decode(raw, type=WorkerRequest)
        except (msgspec.DecodeError, msgspec.ValidationError) as exc:
            log.warning("invalid worker request: %s", exc)
            resp = make_error_response(
                request_id="unknown",
                code=WorkerErrorCode.INVALID_REQUEST,
                message="Failed to decode request",
                details={"request_id": "unknown"},
            )
            try:
                write_frame(writer, msgspec.msgpack.encode(resp))
                await writer.drain()
            finally:
                writer.close()
                await writer.wait_closed()
            return

        if req.command == "events.stream":
            if self._stream_request is None:
                resp = make_error_response(
                    request_id=req.request_id,
                    code=WorkerErrorCode.UNKNOWN_COMMAND,
                    message="Streaming not supported",
                    details={"command": req.command},
                )
                try:
                    write_frame(writer, msgspec.msgpack.encode(resp))
                    await writer.drain()
                finally:
                    writer.close()
                    await writer.wait_closed()
                return
            try:
                await self._stream_request(req, writer, reader)
            except Exception:
                log.exception("streaming worker error", extra={"request_id": req.request_id})
            finally:
                writer.close()
                try:
                    await writer.wait_closed()
                except Exception:
                    pass
            return

        try:
            try:
                resp = await self._handle(req)
            except Exception:
                log.exception("unhandled worker error", extra={"request_id": req.request_id, "command": req.command})
                resp = make_error_response(
                    request_id=req.request_id,
                    code=WorkerErrorCode.INTERNAL_ERROR,
                    message="Internal worker error",
                    details={"command": req.command, "request_id": req.request_id},
                    recoverable=False,
                )
            write_frame(writer, msgspec.msgpack.encode(resp))
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    async def _handle(self, req: WorkerRequest) -> WorkerResponse:
        if not req.protocol_version or protocol_major(req.protocol_version) != PROTOCOL_MAJOR:
            return make_error_response(
                request_id=req.request_id,
                code=WorkerErrorCode.INCOMPATIBLE_PROTOCOL,
                message=f"Protocol major {protocol_major(req.protocol_version)} != {PROTOCOL_MAJOR}",
                details={
                    "requested_major": protocol_major(req.protocol_version),
                    "expected_major": PROTOCOL_MAJOR,
                },
                recoverable=False,
            )
        if req.workspace_id != self._workspace_id:
            return make_error_response(
                request_id=req.request_id,
                code=WorkerErrorCode.WORKSPACE_MISMATCH,
                message=f"Workspace mismatch: {req.workspace_id} != {self._workspace_id}",
                details={"requested": req.workspace_id, "expected": self._workspace_id},
                recoverable=False,
            )
        if self._handle_request is None:
            return make_error_response(
                request_id=req.request_id,
                code=WorkerErrorCode.UNKNOWN_COMMAND,
                message=f"Unknown command: {req.command}",
                details={"command": req.command},
                recoverable=False,
            )
        try:
            result = await self._handle_request(req)
            if isinstance(result, msgspec.Struct):
                err_code = getattr(result, "error_code", None)
                if err_code:
                    return make_error_response(
                        request_id=req.request_id,
                        code=err_code,
                        message=getattr(result, "message", "Unknown error"),
                        recoverable=_is_recoverable(err_code),
                    )
                return make_success_response(req.request_id, msgspec.to_builtins(result))
            if isinstance(result, dict):
                if "error_code" in result:
                    return make_error_response(
                        request_id=req.request_id,
                        code=result["error_code"],
                        message=result.get("message", "Unknown error"),
                        recoverable=_is_recoverable(result["error_code"]),
                    )
                return make_success_response(req.request_id, result)
            return make_success_response(req.request_id, {})
        except Exception:
            return make_error_response(
                request_id=req.request_id,
                code=WorkerErrorCode.INTERNAL_ERROR,
                message="Internal worker error",
                details={"command": req.command, "request_id": req.request_id},
                recoverable=False,
            )
