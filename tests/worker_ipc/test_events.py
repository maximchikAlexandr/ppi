import asyncio

import pytest

from ppi.worker_ipc.events import EventHub


@pytest.fixture
def hub() -> EventHub:
    return EventHub(workspace_id="ws-1", worker_id="w-1")


@pytest.mark.asyncio
async def test_broadcast_to_two_subscribers(hub: EventHub) -> None:
    sub1 = await hub.subscribe()
    sub2 = await hub.subscribe()
    await hub.emit("test.event", {"msg": "hello"})

    s1 = hub._subscribers[sub1]
    s2 = hub._subscribers[sub2]

    e1 = await asyncio.wait_for(s1.queue.get(), timeout=0.5)
    e2 = await asyncio.wait_for(s2.queue.get(), timeout=0.5)

    assert e1.event_type == "test.event"
    assert e1.payload == {"msg": "hello"}
    assert e2.event_type == "test.event"


@pytest.mark.asyncio
async def test_subscribed_event_types(hub: EventHub) -> None:
    sub = await hub.subscribe(["analysis.started"])
    await hub.emit("analysis.started", {"run_id": "run-1"})
    await hub.emit("analysis.progress", {"run_id": "run-1"})

    s = hub._subscribers[sub]
    e = await asyncio.wait_for(s.queue.get(), timeout=0.5)
    assert e.event_type == "analysis.started"
    assert s.queue.empty()


@pytest.mark.asyncio
async def test_slow_subscriber_disconnected(hub: EventHub) -> None:
    sub = await hub.subscribe()
    for _ in range(hub._subscribers[sub].queue.maxsize + 1):
        await hub.emit("test.event", {"n": _})
    assert sub not in hub._subscribers
