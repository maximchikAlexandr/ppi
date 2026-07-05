import pytest

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
    assert result["accepted"] is True
    assert result["state"] == "running"
    assert result["run_id"] is not None
    assert runtime.state.value == "busy"


@pytest.mark.asyncio
async def test_duplicate_analysis_start(runtime: WorkerRuntime) -> None:
    req = _FakeReq({"mode": "incremental"})
    result1 = await runtime.handle_analysis_start(req)
    assert result1["state"] == "running"

    result2 = await runtime.handle_analysis_start(req)
    assert result2["state"] == "already_running"
    assert result2["run_id"] == result1["run_id"]
    assert result2["accepted"] is True


@pytest.mark.asyncio
async def test_analysis_cancel_no_active_run(runtime: WorkerRuntime) -> None:
    req = _FakeReq({})
    result = await runtime.handle_analysis_cancel(req)
    assert result["accepted"] is False
    assert "No active analysis" in result["message"]


@pytest.mark.asyncio
async def test_analysis_status_during_run(runtime: WorkerRuntime) -> None:
    start_req = _FakeReq({"mode": "incremental"})
    await runtime.handle_analysis_start(start_req)

    result = await runtime.handle_analysis_status()
    assert result["state"] == "running"
