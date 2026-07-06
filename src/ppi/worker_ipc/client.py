from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator
from typing import Any, Protocol

import msgspec

from ppi.worker_ipc.constants import CLIENT_COMMAND_TIMEOUT_SECONDS, PROTOCOL_VERSION
from ppi.worker_ipc.runtime_paths import Endpoint
from ppi.worker_ipc.framing import read_frame, write_frame
from ppi.worker_ipc.protocol import (
    WorkerError,
    WorkerEvent,
    WorkerRequest,
    WorkerResponse,
)


class WorkerClientError(Exception):
    def __init__(self, error: WorkerError) -> None:
        self.error = error
        super().__init__(error.message)


class WorkerClientProtocol(Protocol):
    """Structural interface for worker clients (used by FastAPI/CLI)."""

    async def health(self) -> dict[str, Any]: ...
    async def workspace_info(self) -> dict[str, Any]: ...
    async def analysis_status(self) -> dict[str, Any]: ...
    async def analysis_start(self, mode: str = "incremental", reason: str = "cli") -> dict[str, Any]: ...
    async def analysis_cancel(self, run_id: str | None = None, reason: str = "user requested cancellation") -> dict[str, Any]: ...
    async def query_execute(
        self, query_name: str, parameters: dict[str, Any] | None = None, limit: int | None = None
    ) -> dict[str, Any]: ...
    async def events_subscribe(self, event_types: list[str] | None = None) -> dict[str, Any]: ...
    async def shutdown(self, reason: str = "user requested stop") -> dict[str, Any]: ...
    async def close(self) -> None: ...


class WorkerClient:
    def __init__(self, endpoint: Endpoint, workspace_id: str) -> None:
        self._endpoint = endpoint
        self._workspace_id = workspace_id
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._connect_lock = asyncio.Lock()

    async def connect(self) -> None:
        await self.close()
        self._reader, self._writer = await asyncio.wait_for(
            asyncio.open_unix_connection(self._endpoint.path),
            timeout=5.0,
        )

    async def close(self) -> None:
        if self._writer is not None:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except Exception:
                pass
            self._reader = None
            self._writer = None

    async def request(
        self,
        command: str,
        payload: dict[str, Any] | None = None,
        timeout: float = CLIENT_COMMAND_TIMEOUT_SECONDS,
    ) -> WorkerResponse:
        async with self._connect_lock:
            await self.connect()
        if self._writer is None:
            raise ConnectionError("Not connected")
        request_id = f"req-{uuid.uuid4().hex[:12]}"
        req = WorkerRequest(
            request_id=request_id,
            protocol_version=PROTOCOL_VERSION,
            workspace_id=self._workspace_id,
            command=command,
            payload=payload or {},
        )
        encoded = msgspec.msgpack.encode(req)
        write_frame(self._writer, encoded)
        await self._writer.drain()
        if self._reader is None:
            raise ConnectionError("Not connected")
        raw = await asyncio.wait_for(read_frame(self._reader), timeout=timeout)
        resp = msgspec.msgpack.decode(raw, type=WorkerResponse)
        return resp

    async def _typed_request(
        self,
        command: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        resp = await self.request(command, payload)
        if not resp.ok:
            raise WorkerClientError(resp.error)
        return resp.result

    async def health(self) -> dict[str, Any]:
        return await self._typed_request("worker.health")

    async def workspace_info(self) -> dict[str, Any]:
        return await self._typed_request("workspace.info")

    async def analysis_status(self) -> dict[str, Any]:
        return await self._typed_request("analysis.status")

    async def analysis_start(self, mode: str = "incremental", reason: str = "cli") -> dict[str, Any]:
        return await self._typed_request("analysis.start", {"mode": mode, "reason": reason})

    async def analysis_cancel(self, run_id: str | None = None, reason: str = "user requested cancellation") -> dict[str, Any]:
        return await self._typed_request("analysis.cancel", {"run_id": run_id, "reason": reason})

    async def query_execute(
        self, query_name: str, parameters: dict[str, Any] | None = None, limit: int | None = None
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"query_name": query_name, "parameters": parameters or {}}
        if limit is not None:
            payload["limit"] = limit
        return await self._typed_request("query.execute", payload)

    async def events_subscribe(self, event_types: list[str] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if event_types is not None:
            payload["event_types"] = event_types
        return await self._typed_request("events.subscribe", payload)

    async def events_stream(
        self, event_types: list[str] | None = None
    ) -> AsyncIterator[WorkerEvent]:
        """Open a long-lived connection and yield ``WorkerEvent`` instances.

        The server holds the connection open and pushes one frame per event.
        Iteration stops when the connection is closed (e.g. on server shutdown
        or when the caller breaks out of the loop).
        """
        reader, writer = await asyncio.wait_for(
            asyncio.open_unix_connection(self._endpoint.path),
            timeout=5.0,
        )
        try:
            request_id = f"req-{uuid.uuid4().hex[:12]}"
            req = WorkerRequest(
                request_id=request_id,
                protocol_version=PROTOCOL_VERSION,
                workspace_id=self._workspace_id,
                command="events.stream",
                payload={"event_types": event_types} if event_types is not None else {},
            )
            write_frame(writer, msgspec.msgpack.encode(req))
            await writer.drain()
            while True:
                try:
                    raw = await read_frame(reader)
                except (asyncio.IncompleteReadError, ConnectionError):
                    break
                if not raw:
                    break
                yield msgspec.msgpack.decode(raw, type=WorkerEvent)
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    async def shutdown(self, reason: str = "user requested stop") -> dict[str, Any]:
        return await self._typed_request("worker.shutdown", {"reason": reason})
