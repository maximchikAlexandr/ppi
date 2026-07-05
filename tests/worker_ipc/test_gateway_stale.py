from pathlib import Path

import pytest

from ppi.worker_ipc.gateway import WorkerGateway
from ppi.worker_ipc.runtime_metadata import RuntimeMetadata, write_metadata
from ppi.worker_ipc.runtime_paths import metadata_path, socket_path


@pytest.mark.asyncio
async def test_metadata_workspace_mismatch(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    from ppi.runtime.paths import project_id_from_repo
    ws_id = project_id_from_repo(repo)
    meta = RuntimeMetadata(
        workspace_id="wrong-ws",
        worker_id="w-1",
        pid=99999,
        endpoint=f"unix://{socket_path(ws_id)}",
        state="idle",
        started_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        last_heartbeat_at="2026-01-01T00:00:00Z",
    )
    write_metadata(metadata_path(ws_id), meta)
    gateway = WorkerGateway(repo)
    client, diag = await gateway.get_client(start_if_missing=False)
    assert client is not None
    assert diag["status"] == "stale"


@pytest.mark.asyncio
async def test_stale_socket_unix_connect_fails(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    from ppi.runtime.paths import project_id_from_repo
    ws_id = project_id_from_repo(repo)
    meta = RuntimeMetadata(
        workspace_id=ws_id,
        worker_id="w-1",
        pid=99999,
        endpoint=f"unix://{socket_path(ws_id)}",
        state="idle",
        started_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
        last_heartbeat_at="2026-01-01T00:00:00Z",
    )
    write_metadata(metadata_path(ws_id), meta)
    gateway = WorkerGateway(repo)
    client, diag = await gateway.get_client(start_if_missing=False)
    assert client is not None
    assert diag["status"] == "stale"
