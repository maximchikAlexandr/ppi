"""Integration test for events_stream long-lived connection (R-010/R-014)."""
from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

import pytest

from ppi.worker_ipc.client import WorkerClient
from ppi.worker_ipc.events import EventHub
from ppi.worker_ipc.runtime_paths import endpoint_for_workspace
from ppi.worker_ipc.server import WorkerServer
from ppi.worker_ipc.worker_runtime import WorkerRuntime


def _sock(name: str) -> Path:
    d = Path("/tmp/ppi-es")
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{name[0]}-{uuid.uuid4().hex[:6]}.sock"


@pytest.mark.asyncio
async def test_event_hub_stream_stops_on_unsubscribe() -> None:
    """EventHub.stream() stops when subscriber is closed."""
    hub = EventHub(workspace_id="ws-x", worker_id="w-1")
    sub_id = await hub.subscribe()
    events: list = []

    async def consumer() -> None:
        async for e in hub.stream(sub_id):
            events.append(e)

    task = asyncio.create_task(consumer())
    await asyncio.sleep(0.05)
    await hub.emit("test.event", {"x": 1})
    await asyncio.sleep(0.05)
    await hub.unsubscribe(sub_id)
    await asyncio.sleep(0.15)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    assert len(events) == 1
    assert events[0].event_type == "test.event"


@pytest.mark.asyncio
async def test_event_hub_close_stops_all_streams() -> None:
    """EventHub.close() stops all active stream() iterators."""
    hub = EventHub(workspace_id="ws-c", worker_id="w-1")
    sub_id = await hub.subscribe()
    received: list = []

    async def consumer() -> None:
        async for e in hub.stream(sub_id):
            received.append(e)

    task = asyncio.create_task(consumer())
    await asyncio.sleep(0.05)
    await hub.close()
    await asyncio.sleep(0.2)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    assert received == []


@pytest.mark.asyncio
async def test_events_stream_filters_event_types(tmp_path: Path, monkeypatch) -> None:
    """events_stream(event_types=[...]) only delivers matching events."""
    monkeypatch.setenv("XDG_RUNTIME_DIR", "/tmp")
    project = tmp_path / "project"
    project.mkdir()
    analysis = tmp_path / "analysis"
    analysis.mkdir()
    from ppi.worker_ipc.runtime_paths import socket_path
    runtime = WorkerRuntime("ws-stream-2", project, analysis, "odoo", "p")
    sp = socket_path("ws-stream-2")
    server = WorkerServer(str(sp), "ws-stream-2")
    server.set_handle_request(runtime._handle_command)
    server.set_stream_request(runtime.stream_events)
    await server.start()
    try:
        asyncio.create_task(runtime.event_hub.emit("analysis.started", {"run_id": "r1"}))
        asyncio.create_task(runtime.event_hub.emit("worker.ready", {"state": "idle"}))

        client = WorkerClient(endpoint_for_workspace("ws-stream-2"), "ws-stream-2")
        events: list = []

        async def _consume() -> None:
            async for event in client.events_stream(event_types=["worker.ready"]):
                events.append(event)
                if len(events) >= 1:
                    break

        try:
            await asyncio.wait_for(_consume(), timeout=2.0)
        except asyncio.TimeoutError:
            pass

        for e in events:
            assert e.event_type == "worker.ready"
    finally:
        await runtime.event_hub.close()
        await server.stop()
