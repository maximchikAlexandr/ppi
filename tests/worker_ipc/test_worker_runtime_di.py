"""Tests for F-010 dependency injection on WorkerRuntime.

Verifies that the runtime can be constructed with fake services
and that handlers use the injected services rather than instantiating
real ones.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pytest

from ppi.worker_ipc.worker_runtime import WorkerRuntime


class FakeAnalysisService:
    """In-memory replacement for AnalysisService used in DI tests."""

    def __init__(self) -> None:
        self.run_called = 0
        self.last_mode: str | None = None

    async def run(
        self,
        run_id: str,
        progress: Callable | None = None,
        should_cancel: Callable[[], bool] | None = None,
        mode: str = "incremental",
        progress_callback: Callable[[float, str], None] | None = None,
    ) -> None:
        self.run_called += 1
        self.last_mode = mode
        if progress_callback is not None:
            progress_callback(100.0, "fake done")


class FakeQueryService:
    """In-memory replacement for QueryService used in DI tests."""

    def __init__(self) -> None:
        self.executed: list[tuple[str, dict, int | None]] = []

    async def execute(
        self,
        query_name: str,
        parameters: dict | None = None,
        limit: int | None = None,
    ) -> dict:
        self.executed.append((query_name, parameters or {}, limit))
        return {"columns": ["x"], "rows": [{"x": 1}], "row_count": 1, "truncated": False}


def _make_req(command: str, payload: dict | None = None):
    class Req:
        def __init__(self) -> None:
            self.command = command
            self.payload = payload or {}

    return Req()


@pytest.mark.asyncio
async def test_worker_runtime_uses_injected_analysis_service(tmp_path: Path) -> None:
    fake = FakeAnalysisService()
    runtime = WorkerRuntime(
        workspace_id="ws-di",
        project_path=tmp_path / "proj",
        analysis_path=tmp_path,
        profile="odoo",
        display_name="x",
        analysis_service=fake,
    )
    resp = await runtime.handle_analysis_start(_make_req("analysis.start", {"mode": "incremental"}))
    assert resp.accepted is True
    assert resp.state == "running"

    await runtime._analysis_task

    assert fake.run_called == 1
    assert fake.last_mode == "incremental"


@pytest.mark.asyncio
async def test_worker_runtime_uses_injected_query_service(tmp_path: Path) -> None:
    fake = FakeQueryService()
    runtime = WorkerRuntime(
        workspace_id="ws-di",
        project_path=tmp_path / "proj",
        analysis_path=tmp_path,
        profile="odoo",
        display_name="x",
        query_service=fake,
    )
    resp = await runtime.handle_query_execute(
        _make_req("query.execute", {"query_name": "commits", "parameters": {"x": 1}, "limit": 5})
    )
    assert resp.row_count == 1
    assert fake.executed == [("commits", {"x": 1}, 5)]


@pytest.mark.asyncio
async def test_worker_runtime_uses_injected_clock_and_id_generator(tmp_path: Path) -> None:
    fixed_time = datetime(2026, 1, 1, tzinfo=UTC)

    def fixed_clock() -> datetime:
        return fixed_time

    counter = {"n": 0}

    def fixed_id() -> str:
        counter["n"] += 1
        return f"w-{counter['n']}"

    runtime = WorkerRuntime(
        workspace_id="ws-clock",
        project_path=tmp_path / "proj",
        analysis_path=tmp_path,
        profile="odoo",
        display_name="x",
        clock=fixed_clock,
        id_generator=fixed_id,
    )
    assert runtime.worker_id == "w-1"
    assert runtime.started_at == "2026-01-01T00:00:00+00:00"

    runtime2 = WorkerRuntime(
        workspace_id="ws-clock-2",
        project_path=tmp_path / "proj",
        analysis_path=tmp_path,
        profile="odoo",
        display_name="x",
        clock=fixed_clock,
        id_generator=fixed_id,
    )
    assert runtime2.worker_id == "w-2"
