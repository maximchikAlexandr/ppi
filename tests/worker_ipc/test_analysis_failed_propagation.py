"""Test that AnalysisService.run() failure status is propagated to runtime."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from ppi.worker_ipc.analysis_service import AnalysisRunResult
from ppi.worker_ipc.worker_runtime import WorkerRuntime


class _Req:
    def __init__(self, payload: dict) -> None:
        self.payload = payload


class FakeFailingAnalysisService:
    """Service that always returns status="failed"."""

    def __init__(self) -> None:
        self.run_called = 0

    async def run(
        self,
        run_id: str,
        progress: Callable | None = None,
        should_cancel: Callable[[], bool] | None = None,
        mode: str = "incremental",
        progress_callback: Callable | None = None,
    ) -> AnalysisRunResult:
        self.run_called += 1
        return AnalysisRunResult(
            run_id=run_id,
            status="failed",
            commits_total=0,
            commits_succeeded=0,
            commits_failed=0,
        )


@pytest.mark.asyncio
async def test_analysis_failed_status_propagates_to_runtime(tmp_path: Path) -> None:
    """If AnalysisService.run() returns status=failed, runtime must report failed."""
    fake = FakeFailingAnalysisService()
    runtime = WorkerRuntime(
        workspace_id="ws-fail",
        project_path=tmp_path / "proj",
        analysis_path=tmp_path,
        profile="odoo",
        display_name="x",
        analysis_service=fake,
    )
    resp = await runtime.handle_analysis_start(_Req({"mode": "incremental"}))
    assert resp.accepted is True
    await runtime._analysis_task

    status = await runtime.handle_analysis_status()
    assert status.state == "failed", f"expected failed, got {status.state}"
    assert "failed" in status.message.lower() or "0/0" in status.message


class FakeCancelledAnalysisService:
    """Service that ignores should_cancel but sets _cancel_flag on the runtime."""

    def __init__(self) -> None:
        self.run_called = 0
        self.runtime_ref: list = []

    async def run(
        self,
        run_id: str,
        progress: Callable | None = None,
        should_cancel: Callable[[], bool] | None = None,
        mode: str = "incremental",
        progress_callback: Callable | None = None,
    ) -> AnalysisRunResult:
        self.run_called += 1
        if self.runtime_ref:
            self.runtime_ref[0]._cancel_flag = True
        return AnalysisRunResult(
            run_id=run_id,
            status="completed",
            commits_total=0,
            commits_succeeded=0,
            commits_failed=0,
        )


@pytest.mark.asyncio
async def test_analysis_cancelled_status_propagates_to_runtime(tmp_path: Path) -> None:
    """If _cancel_flag triggers, runtime must report cancelled even if service returns completed."""
    fake = FakeCancelledAnalysisService()
    runtime = WorkerRuntime(
        workspace_id="ws-cancel",
        project_path=tmp_path / "proj",
        analysis_path=tmp_path,
        profile="odoo",
        display_name="x",
        analysis_service=fake,
    )
    fake.runtime_ref.append(runtime)
    resp = await runtime.handle_analysis_start(_Req({"mode": "incremental"}))
    assert resp.accepted is True
    await runtime._analysis_task

    status = await runtime.handle_analysis_status()
    assert status.state == "cancelled", f"expected cancelled, got {status.state}"
