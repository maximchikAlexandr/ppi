from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any

from ppi.worker_ipc.constants import EVENT_QUEUE_MAXSIZE
from ppi.worker_ipc.protocol import WorkerEvent


class _Subscriber:
    def __init__(self, subscriber_id: str, event_types: set[str] | None = None) -> None:
        self.subscriber_id = subscriber_id
        self.event_types = event_types
        self.queue: asyncio.Queue[WorkerEvent] = asyncio.Queue(maxsize=EVENT_QUEUE_MAXSIZE)


class EventHub:
    def __init__(self, workspace_id: str, worker_id: str) -> None:
        self._workspace_id = workspace_id
        self._worker_id = worker_id
        self._subscribers: dict[str, _Subscriber] = {}
        self._lock = asyncio.Lock()

    def _make_event(self, event_type: str, payload: dict[str, Any]) -> WorkerEvent:
        return WorkerEvent(
            event_id=f"evt-{uuid.uuid4().hex[:12]}",
            workspace_id=self._workspace_id,
            worker_id=self._worker_id,
            event_type=event_type,
            created_at=datetime.now(UTC).isoformat(),
            payload=payload,
        )

    async def subscribe(self, event_types: list[str] | None = None) -> str:
        sub_id = f"sub-{uuid.uuid4().hex[:8]}"
        types_set = set(event_types) if event_types else None
        async with self._lock:
            self._subscribers[sub_id] = _Subscriber(sub_id, types_set)
        return sub_id

    async def unsubscribe(self, sub_id: str) -> None:
        async with self._lock:
            self._subscribers.pop(sub_id, None)

    async def emit(self, event_type: str, payload: dict[str, Any]) -> None:
        event = self._make_event(event_type, payload)
        async with self._lock:
            to_remove: list[str] = []
            for sub_id, sub in list(self._subscribers.items()):
                if sub.event_types is not None and event_type not in sub.event_types:
                    continue
                try:
                    sub.queue.put_nowait(event)
                except asyncio.QueueFull:
                    to_remove.append(sub_id)
            for sub_id in to_remove:
                self._subscribers.pop(sub_id, None)

    def event_types_for(self, sub_id: str) -> set[str] | None:
        sub = self._subscribers.get(sub_id)
        return sub.event_types if sub else None


