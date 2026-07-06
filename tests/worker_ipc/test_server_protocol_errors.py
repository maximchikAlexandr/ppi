import asyncio
import os
import uuid
from pathlib import Path

import msgspec
import pytest

from ppi.worker_ipc.constants import PROTOCOL_VERSION
from ppi.worker_ipc.framing import read_frame, write_frame
from ppi.worker_ipc.protocol import WorkerRequest
from ppi.worker_ipc.server import WorkerServer


def _sock(name: str) -> Path:
    d = Path(f"/tmp/ppi-test-{os.getpid()}")
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{name}-{uuid.uuid4().hex[:8]}.sock"


async def _connect_client(socket_path: Path):
    reader, writer = await asyncio.open_unix_connection(str(socket_path))
    return reader, writer


async def _send_and_receive(writer: asyncio.StreamWriter, reader: asyncio.StreamReader, data: bytes) -> bytes:
    write_frame(writer, data)
    await writer.drain()
    return await read_frame(reader)


@pytest.mark.asyncio
async def test_invalid_request() -> None:
    socket_path = _sock("invalid")
    server = WorkerServer(str(socket_path), "ws-1")
    await server.start()
    reader, writer = await _connect_client(socket_path)
    write_frame(writer, b"not-valid-msgspec")
    await writer.drain()
    raw = await read_frame(reader)
    resp = msgspec.msgpack.decode(raw)
    writer.close()
    await writer.wait_closed()
    assert resp["ok"] is False
    assert resp["error"]["code"] == "INVALID_REQUEST"
    await server.stop()


@pytest.mark.asyncio
async def test_unknown_command() -> None:
    socket_path = _sock("unknown")
    server = WorkerServer(str(socket_path), "ws-1")
    await server.start()
    reader, writer = await _connect_client(socket_path)
    req = WorkerRequest(
        request_id="req-1",
        protocol_version=PROTOCOL_VERSION,
        workspace_id="ws-1",
        command="nonexistent.cmd",
        payload={},
    )
    raw = await _send_and_receive(writer, reader, msgspec.msgpack.encode(req))
    resp = msgspec.msgpack.decode(raw)
    writer.close()
    await writer.wait_closed()
    assert resp["ok"] is False
    assert resp["error"]["code"] == "UNKNOWN_COMMAND"
    await server.stop()


@pytest.mark.asyncio
async def test_workspace_mismatch() -> None:
    socket_path = _sock("wsm")
    server = WorkerServer(str(socket_path), "expected-ws")
    await server.start()
    reader, writer = await _connect_client(socket_path)
    req = WorkerRequest(
        request_id="req-1",
        protocol_version=PROTOCOL_VERSION,
        workspace_id="wrong-ws",
        command="worker.health",
        payload={},
    )
    raw = await _send_and_receive(writer, reader, msgspec.msgpack.encode(req))
    resp = msgspec.msgpack.decode(raw)
    writer.close()
    await writer.wait_closed()
    assert resp["ok"] is False
    assert resp["error"]["code"] == "WORKSPACE_MISMATCH"
    await server.stop()


@pytest.mark.asyncio
async def test_protocol_mismatch() -> None:
    socket_path = _sock("proto")
    server = WorkerServer(str(socket_path), "ws-1")
    await server.start()
    reader, writer = await _connect_client(socket_path)
    req = WorkerRequest(
        request_id="req-1",
        protocol_version="2.0",
        workspace_id="ws-1",
        command="worker.health",
        payload={},
    )
    raw = await _send_and_receive(writer, reader, msgspec.msgpack.encode(req))
    resp = msgspec.msgpack.decode(raw)
    writer.close()
    await writer.wait_closed()
    assert resp["ok"] is False
    assert resp["error"]["code"] == "INCOMPATIBLE_PROTOCOL"
    await server.stop()
