from unittest.mock import AsyncMock, patch

import pytest

from ppi.worker_ipc.gateway import GatewayAttachResult, WorkerGateway


@pytest.mark.asyncio
async def test_startup_lock_reattach(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    from ppi.runtime.paths import project_id_from_repo
    from ppi.worker_ipc.runtime_metadata import RuntimeMetadata, write_metadata
    from ppi.worker_ipc.runtime_paths import metadata_path, socket_path

    ws_id = project_id_from_repo(repo)
    meta = RuntimeMetadata(
        workspace_id=ws_id,
        worker_id="w-existing",
        pid=12345,
        endpoint=f"unix://{socket_path(ws_id)}",
        state="idle",
        started_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:05Z",
        last_heartbeat_at="2026-01-01T00:00:05Z",
    )
    write_metadata(metadata_path(ws_id), meta)

    with (
        patch("ppi.worker_ipc.gateway.Supervisor.spawn_worker"),
        patch(
            "ppi.worker_ipc.gateway.Supervisor.wait_until_healthy", AsyncMock(return_value=False)
        ),
    ):
        gateway = WorkerGateway(repo)
        result = await gateway.get_client(start_if_missing=True)
        assert result.client is None
        assert result.status == "unavailable"


@pytest.mark.asyncio
async def test_configuration_mismatch_never_marks_live_worker_stale_or_spawns(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    mismatch = GatewayAttachResult(
        client=None,
        status="configuration_mismatch",
        message="different runtime configuration",
    )
    gateway = WorkerGateway(repo)
    with (
        patch.object(gateway, "_try_connect", AsyncMock(return_value=mismatch)),
        patch("ppi.worker_ipc.gateway.mark_stale") as mark_stale,
        patch("ppi.worker_ipc.gateway.Supervisor.spawn_worker") as spawn,
    ):
        result = await gateway.get_client(start_if_missing=True)

    assert result.status == "configuration_mismatch"
    mark_stale.assert_not_called()
    spawn.assert_not_called()
