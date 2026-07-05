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
async def test_query_execute_returns_busy_during_analysis(runtime: WorkerRuntime) -> None:
    start_req = _FakeReq({"mode": "incremental"})
    await runtime.handle_analysis_start(start_req)

    req = _FakeReq({"query_name": "commits", "parameters": {}})
    result = await runtime.handle_query_execute(req)
    assert result.get("error_code") == "WORKER_BUSY"
