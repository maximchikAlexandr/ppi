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


@pytest.mark.asyncio
async def test_health_handler(runtime: WorkerRuntime) -> None:
    result = await runtime.handle_health()
    assert result["worker_id"] == runtime.worker_id
    assert result["workspace_id"] == "ws-1"
    assert result["protocol_version"] == "1.0"
    assert "state" in result


@pytest.mark.asyncio
async def test_workspace_info_handler(runtime: WorkerRuntime) -> None:
    result = await runtime.handle_workspace_info()
    assert result["workspace_id"] == "ws-1"
    assert result["project_path"] is not None
    assert result["profile"] == "odoo"
    assert result["display_name"] == "project"


@pytest.mark.asyncio
async def test_analysis_status_not_started(runtime: WorkerRuntime) -> None:
    result = await runtime.handle_analysis_status()
    assert "state" in result
    assert "message" in result


@pytest.mark.asyncio
async def test_worker_shutdown_idle(runtime: WorkerRuntime) -> None:
    runtime.state = "idle"
    result = await runtime.shutdown()
    assert result["accepted"] is True
    assert "shutdown accepted" in result["message"].lower()
