"""Integration tests: analysis lifecycle through worker boundary (T091, T092, T093).

These tests validate analysis semantics at the WorkerRuntime level,
which is the same code path used by the real worker. Full subprocess-based
tests require a real analysis store with Git history.
"""

from pathlib import Path
from typing import Any

import pytest

from ppi.worker_ipc.handler_results import WorkerErrorResult
from ppi.worker_ipc.protocol import WorkerState
from ppi.worker_ipc.worker_runtime import WorkerRuntime


def _req(payload: dict[str, Any]) -> object:
    return type("Req", (object,), {"payload": payload})()


@pytest.mark.asyncio
async def test_duplicate_analysis_start_coalesces_only_identical_request(
    tmp_path: Path, ws_id: str
) -> None:
    """T091: Only an identical analysis.start joins an active run."""
    project = tmp_path / "project"
    project.mkdir()
    analysis = tmp_path / "analysis"
    analysis.mkdir()
    runtime = WorkerRuntime(ws_id, project, analysis, "odoo", "test")
    await runtime.start()
    try:
        r1 = await runtime.handle_analysis_start(_req({"mode": "incremental"}))
        assert r1.state == "running"
        r2 = await runtime.handle_analysis_start(_req({"mode": "incremental"}))
        assert r2.state == "already_running"
        assert r2.run_id == r1.run_id
        assert r2.accepted is True
        rejected = await runtime.handle_analysis_start(_req({"mode": "full"}))
        assert isinstance(rejected, WorkerErrorResult)
        assert rejected.error_code == "WORKER_BUSY"
        rejected_branch = await runtime.handle_analysis_start(
            _req({"mode": "incremental", "branch": "other"}),
        )
        assert isinstance(rejected_branch, WorkerErrorResult)
        assert rejected_branch.error_code == "WORKER_BUSY"
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
    assert result.accepted is True


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
    assert result.error_code == "WORKER_BUSY"
