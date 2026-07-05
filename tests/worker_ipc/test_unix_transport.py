import asyncio
import os
import uuid
from pathlib import Path

import pytest

from ppi.worker_ipc.framing import read_frame, write_frame


def _sock(name: str) -> Path:
    d = Path(f"/tmp/ppi-test-{os.getpid()}")
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{name}-{uuid.uuid4().hex[:8]}.sock"


@pytest.mark.asyncio
async def test_client_server_exchange() -> None:
    socket_path = _sock("exch")
    received: list[bytes] = []

    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        payload = await read_frame(reader)
        received.append(payload)
        write_frame(writer, b"pong")
        await writer.drain()
        writer.close()

    server = await asyncio.start_unix_server(handler, path=str(socket_path))
    reader, writer = await asyncio.open_unix_connection(str(socket_path))
    write_frame(writer, b"ping")
    await writer.drain()
    response = await read_frame(reader)
    assert response == b"pong"
    assert received == [b"ping"]

    writer.close()
    await writer.wait_closed()
    server.close()
    await server.wait_closed()
