import asyncio

import pytest

from ppi.worker_ipc.events import EventHub


@pytest.fixture
def hub() -> EventHub:
    return EventHub(workspace_id="ws-1", worker_id="w-1")


@pytest.mark.asyncio
async def test_subscribed_client_receives_events(hub: EventHub) -> None:
    sub_id = await hub.subscribe(["analysis.started", "analysis.progress"])
    await hub.emit("analysis.started", {"run_id": "run-1", "mode": "incremental"})
    await hub.emit("analysis.progress", {"run_id": "run-1", "progress_percent": 50.0})

    s = hub._subscribers[sub_id]
    e1 = await asyncio.wait_for(s.queue.get(), timeout=0.5)
    e2 = await asyncio.wait_for(s.queue.get(), timeout=0.5)
    assert e1.event_type == "analysis.started"
    assert e2.event_type == "analysis.progress"
