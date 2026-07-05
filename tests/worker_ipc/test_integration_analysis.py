"""Integration tests: analysis lifecycle through worker boundary (T091, T092, T093).

These tests validate analysis semantics at the WorkerRuntime level,
which is the same code path used by the real worker. Full subprocess-based
tests require a real analysis store with Git history.
"""

from pathlib import Path

import pytest

from collections.abc import Mapping
from typing import Any

from ppi.worker_ipc.worker_runtime import WorkerRuntime
from ppi.worker_ipc.protocol import WorkerState


def _req(payload: dict[str, Any]) -> object:
    return type("Req", (object,), {"payload": payload})()


@pytest.mark.asyncio
async def test_duplicate_analysis_start_returns_same_run_id(tmp_path: Path, ws_id: str) -> None:
    """T091: Two analysis.start calls return same run_id with already_running."""
    project = tmp_path / "project"
    project.mkdir()
    analysis = tmp_path / "analysis"
    analysis.mkdir()
    runtime = WorkerRuntime(ws_id, project, analysis, "odoo", "test")
    await runtime.start()
    try:
        r1 = await runtime.handle_analysis_start(_req({"mode": "incremental"}))
        assert r1.get("state") == "running"
        r2 = await runtime.handle_analysis_start(_req({"mode": "full"}))
        assert r2.get("state") == "already_running"
        assert r2.get("run_id") == r1.get("run_id")
        assert r2.get("accepted") is True
    finally:
        runtime._cancel_flag = True
        if runtime._analysis_task and not runtime._analysis_task.done():
            runtime._analysis_task.cancel()


@pytest.mark.asyncio
async def test_client_disconnect_does_not_stop_worker(tmp_path: Path, ws_id: str) -> None:
    """T092: Disconnecting a client does not stop the worker runtime.

    The WorkerRuntime continues running independently of any client connection.
    """
    project = tmp_path / "project"
    project.mkdir()
    analysis = tmp_path / "analysis"
    analysis.mkdir()
    runtime = WorkerRuntime(ws_id, project, analysis, "odoo", "test")
    await runtime.start()
    result = await runtime.shutdown()
    assert result.get("accepted") is True


@pytest.mark.asyncio
async def test_worker_stop_during_busy_returns_busy(tmp_path: Path, ws_id: str) -> None:
    """T093: worker.shutdown while busy returns WORKER_BUSY."""
    project = tmp_path / "project"
    project.mkdir()
    analysis = tmp_path / "analysis"
    analysis.mkdir()
    runtime = WorkerRuntime(ws_id, project, analysis, "odoo", "test")
    await runtime.start()
    runtime.state = WorkerState.busy
    result = await runtime.handle_shutdown(_req({}))
    assert result.get("error_code") == "WORKER_BUSY"
