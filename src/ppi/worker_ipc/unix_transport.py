"""Unix-domain-socket transport layer.

Thin wrapper over ``asyncio.open_unix_connection`` and
``asyncio.start_unix_server`` that exposes a single connection object
for clients and a single server object for the request-handling
event loop.

Transport is intentionally command-agnostic: it sends and receives
raw bytes only. It does not know about ``worker.health``,
``analysis.start``, workspace IDs, or runtime state.
"""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path

from ppi.worker_ipc.framing import read_frame, write_frame


class UnixClientTransport:
    """Single-connection transport that talks raw bytes over a Unix socket."""

    def __init__(self, socket_path: Path) -> None:
        self._socket_path = socket_path
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    async def connect(self) -> None:
        self._reader, self._writer = await asyncio.wait_for(
            asyncio.open_unix_connection(str(self._socket_path)),
            timeout=5.0,
        )

    async def request_bytes(self, payload: bytes) -> bytes:
        """Send one framed message and read back one framed response."""
        if self._writer is None or self._reader is None:
            raise ConnectionError(f"not connected to {self._socket_path}")
        write_frame(self._writer, payload)
        await self._writer.drain()
        return await read_frame(self._reader)

    async def close(self) -> None:
        if self._writer is not None:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except Exception:
                pass
            self._writer = None
            self._reader = None


class UnixServerTransport:
    """Server-side transport that accepts connections and dispatches to a
    byte-level handler. The handler is given a single request payload
    and returns a single response payload.
    """

    def __init__(
        self,
        socket_path: Path,
        handler: Callable[[bytes], Awaitable[bytes]],
    ) -> None:
        self._socket_path = socket_path
        self._handler = handler
        self._server: asyncio.AbstractServer | None = None

    async def start(self, *, force: bool = False) -> None:
        """Start the server.

        By default does NOT unlink an existing socket; the caller is
        responsible for verifying the socket is stale (e.g. after
        gateway health-check failure + startup lock acquisition) and
        passing ``force=True`` to unlink and rebind.
        """
        self._socket_path.parent.mkdir(parents=True, exist_ok=True)
        if self._socket_path.exists():
            if not force:
                raise FileExistsError(
                    f"Socket {self._socket_path} already exists; pass force=True to unlink stale"
                )
            self._socket_path.unlink()
        self._server = await asyncio.start_unix_server(
            self._serve, path=str(self._socket_path)
        )

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def _serve(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        try:
            payload = await read_frame(reader)
            response = await self._handler(payload)
            write_frame(writer, response)
            await writer.drain()
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
