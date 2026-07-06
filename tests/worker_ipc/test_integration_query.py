"""Integration test: worker-backed query execution (T105).

Tests query execution through the WorkerRuntime dispatch path,
which is the same code path used by the real worker process.
"""

from pathlib import Path

import pytest

from ppi.worker_ipc.worker_runtime import WorkerRuntime
from ppi.worker_ipc.protocol import WorkerState, WorkerErrorCode


def _req(payload: dict) -> object:
    return type("Req", (object,), {"payload": payload})()


@pytest.mark.asyncio
async def test_query_refused_when_busy(tmp_path: Path, ws_id: str) -> None:
    """Worker-backed query returns WORKER_BUSY during analysis."""
    project = tmp_path / "project"
    project.mkdir()
    analysis = tmp_path / "analysis"
    analysis.mkdir()
    runtime = WorkerRuntime(ws_id, project, analysis, "odoo", "test")
    await runtime.start()
    runtime.state = WorkerState.busy
    result = await runtime.handle_query_execute(_req({"query_name": "project/info", "parameters": {}}))
    assert result.error_code == WorkerErrorCode.WORKER_BUSY.value


@pytest.mark.asyncio
async def test_query_unknown_name(tmp_path: Path, ws_id: str) -> None:
    """Worker-backed query with unknown name returns UNKNOWN_QUERY."""
    project = tmp_path / "project"
    project.mkdir()
    analysis = tmp_path / "analysis"
    analysis.mkdir()
    runtime = WorkerRuntime(ws_id, project, analysis, "odoo", "test")
    await runtime.start()
    result = await runtime.handle_query_execute(_req({"query_name": "nonexistent_query", "parameters": {}}))
    assert getattr(result, "error_code", None) is not None, f"Expected error for unknown query, got {result}"
