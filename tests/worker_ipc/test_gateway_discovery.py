import pytest

from ppi.worker_ipc.gateway import WorkerGateway


@pytest.mark.asyncio
async def test_no_start_unavailable(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    gateway = WorkerGateway(repo)
    client, diag = await gateway.get_client(start_if_missing=False)
    assert client is None
    assert diag["status"] == "unavailable"
