import pytest

from ppi.worker_ipc.analysis_service import AnalysisRunResult
from ppi.worker_ipc.handler_results import WorkerErrorResult
from ppi.worker_ipc.worker_runtime import WorkerRuntime


@pytest.fixture
def runtime(tmp_path) -> WorkerRuntime:
    return WorkerRuntime(
        workspace_id="ws-1",
        project_path=tmp_path / "project",
        analysis_path=tmp_path / "analysis",
        profile="odoo",
        display_name="project",
    )


class _FakeReq:
    def __init__(self, payload: dict):
        self.payload = payload


@pytest.mark.asyncio
async def test_analysis_start_creates_run(runtime: WorkerRuntime) -> None:
    req = _FakeReq({"mode": "incremental", "reason": "test"})
    result = await runtime.handle_analysis_start(req)
    assert result.accepted is True
    assert result.state == "running"
    assert result.run_id is not None
    assert runtime.state.value == "busy"


@pytest.mark.asyncio
async def test_duplicate_analysis_start(runtime: WorkerRuntime) -> None:
    req = _FakeReq({"mode": "incremental"})
    result1 = await runtime.handle_analysis_start(req)
    assert result1.state == "running"

    result2 = await runtime.handle_analysis_start(req)
    assert result2.state == "already_running"
    assert result2.run_id == result1.run_id
    assert result2.accepted is True


@pytest.mark.asyncio
async def test_analysis_cancel_no_active_run(runtime: WorkerRuntime) -> None:
    req = _FakeReq({})
    result = await runtime.handle_analysis_cancel(req)
    assert result.accepted is False
    assert "No active analysis" in result.message


@pytest.mark.asyncio
async def test_analysis_start_rejects_malformed_typed_payload(runtime: WorkerRuntime) -> None:
    result = await runtime.handle_analysis_start(_FakeReq({"mode": ["invalid"]}))
    assert isinstance(result, WorkerErrorResult)
    assert result.error_code == "INVALID_REQUEST"


@pytest.mark.asyncio
async def test_analysis_start_rejects_unknown_mode(runtime: WorkerRuntime) -> None:
    result = await runtime.handle_analysis_start(_FakeReq({"mode": "rebuild"}))
    assert isinstance(result, WorkerErrorResult)
    assert result.error_code == "INVALID_REQUEST"


@pytest.mark.asyncio
async def test_analysis_status_during_run(runtime: WorkerRuntime) -> None:
    start_req = _FakeReq({"mode": "incremental"})
    await runtime.handle_analysis_start(start_req)

    result = await runtime.handle_analysis_status()
    assert result.state == "running"


@pytest.mark.asyncio
async def test_completed_partial_failure_is_visible_in_human_summary(tmp_path) -> None:
    class _Service:
        async def run(self, **_kwargs):
            return AnalysisRunResult("run", "completed", 2, 1, 1)

    runtime = WorkerRuntime(
        "ws-summary",
        tmp_path / "project",
        tmp_path / "analysis",
        "odoo",
        "p",
        analysis_service=_Service(),
    )
    await runtime.handle_analysis_start(_FakeReq({"mode": "incremental", "branch": "main"}))
    await runtime._analysis_task
    status = await runtime.handle_analysis_status()
    assert status.state == "completed"
    assert "failed: 1" in status.message
