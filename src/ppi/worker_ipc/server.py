from __future__ import annotations

import asyncio
import traceback
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

    def set_handle_request(
        self,
        handler: Callable[[WorkerRequest], Awaitable[dict[str, Any]]],
    ) -> None:
        self._handle_request = handler

    async def start(self) -> None:
        path = Path(self._socket_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
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
            resp = make_error_response(
                request_id="unknown",
                code=WorkerErrorCode.INVALID_REQUEST,
                message=f"Failed to decode request: {exc}",
                details={"parse_error": str(exc)},
            )
            try:
                write_frame(writer, msgspec.msgpack.encode(resp))
                await writer.drain()
            finally:
                writer.close()
                await writer.wait_closed()
            return

        try:
            try:
                resp = await self._handle(req)
            except Exception as exc:
                resp = make_error_response(
                    request_id=req.request_id,
                    code=WorkerErrorCode.INTERNAL_ERROR,
                    message=f"Unhandled error: {exc}",
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
            )
        if req.workspace_id != self._workspace_id:
            return make_error_response(
                request_id=req.request_id,
                code=WorkerErrorCode.WORKSPACE_MISMATCH,
                message=f"Workspace mismatch: {req.workspace_id} != {self._workspace_id}",
                details={"requested": req.workspace_id, "expected": self._workspace_id},
            )
        if self._handle_request is None:
            return make_error_response(
                request_id=req.request_id,
                code=WorkerErrorCode.UNKNOWN_COMMAND,
                message=f"Unknown command: {req.command}",
                details={"command": req.command},
            )
        try:
            result = await self._handle_request(req)
            if isinstance(result, dict) and "error_code" in result:
                return make_error_response(
                    request_id=req.request_id,
                    code=result["error_code"],
                    message=result.get("message", "Unknown error"),
                )
            return make_success_response(req.request_id, result)
        except Exception as exc:
            return make_error_response(
                request_id=req.request_id,
                code=WorkerErrorCode.INTERNAL_ERROR,
                message=str(exc),
                details={"traceback": traceback.format_exc()[-2000:]},
            )
