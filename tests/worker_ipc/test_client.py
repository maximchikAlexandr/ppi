import asyncio
import os
import uuid
from pathlib import Path

import msgspec
import pytest

from ppi.worker_ipc.client import WorkerClient
from ppi.worker_ipc.runtime_paths import Endpoint
from ppi.worker_ipc.framing import read_frame, write_frame
from ppi.worker_ipc.protocol import (
    WorkerRequest,
    WorkerResponse,
    make_error_response,
    make_success_response,
)


@pytest.fixture
def ws_id() -> str:
    return "test-ws"


def _sock(name: str) -> Path:
    d = Path(f"/tmp/ppi-test-{os.getpid()}")
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{name}-{uuid.uuid4().hex[:8]}.sock"


async def _start_test_server(socket_path: Path, responses: list[WorkerResponse]):
    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        raw = await read_frame(reader)
        req = msgspec.msgpack.decode(raw, type=WorkerRequest)
        resp = responses.pop(0) if responses else make_success_response(req.request_id)
        write_frame(writer, msgspec.msgpack.encode(resp))
        await writer.drain()
        writer.close()

    server = await asyncio.start_unix_server(handler, path=str(socket_path))
    return server


@pytest.mark.asyncio
async def test_success_response(ws_id: str) -> None:
    socket_path = _sock("succ")
    ep = Endpoint(transport="unix", path=str(socket_path))
    responses = [make_success_response("req-1", {"worker_id": "w-1", "state": "idle"})]
    server = await _start_test_server(socket_path, responses)
    client = WorkerClient(ep, ws_id)
    result = await client.health()
    assert result["state"] == "idle"
    await client.close()
    server.close()
    await server.wait_closed()


@pytest.mark.asyncio
async def test_structured_error(ws_id: str) -> None:
    socket_path = _sock("err")
    ep = Endpoint(transport="unix", path=str(socket_path))
    responses = [
            make_error_response("req-1", "WORKER_BUSY", "Worker is busy")
    ]
    server = await _start_test_server(socket_path, responses)
    client = WorkerClient(ep, ws_id)
    from ppi.worker_ipc.client import WorkerClientError
    with pytest.raises(WorkerClientError) as exc_info:
        await client.health()
    assert exc_info.value.error.code == "WORKER_BUSY"
    await client.close()
    server.close()
    await server.wait_closed()
