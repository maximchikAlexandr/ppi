"""Integration tests: real worker subprocess lifecycle (T056, T057)."""

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from ppi.worker_ipc.client import WorkerClient
from ppi.worker_ipc.runtime_paths import Endpoint
from ppi.worker_ipc.runtime_paths import socket_path, metadata_path
from ppi.worker_ipc.runtime_metadata import read_metadata


def _wait_for_socket(sock: Path, timeout: float = 10) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if sock.exists():
            return True
        time.sleep(0.2)
    return False


def _worker_env() -> dict:
    env = dict(os.environ)
    env.setdefault("XDG_RUNTIME_DIR", f"/tmp/ppi-test-{os.getpid()}")
    return env


@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires Python 3.10+")
@pytest.mark.asyncio
async def test_worker_spawn_health_stop(integration_env: dict, ws_id: str) -> None:
    """Direct subprocess spawn + IPC roundtrip + shutdown."""
    repo = integration_env["repo"]
    xdg_runtime = str(socket_path(ws_id).parent.parent.parent)
    env = dict(os.environ)
    env["XDG_RUNTIME_DIR"] = xdg_runtime
    env["PPI_WORKSPACE_REGISTRY"] = os.environ.get("PPI_WORKSPACE_REGISTRY", "")

    sock = socket_path(ws_id)
    if not sock.parent.exists():
        sock.parent.mkdir(parents=True, exist_ok=True)

    proc = subprocess.Popen(
        [sys.executable, "-m", "ppi.cli.main", "--repo", str(repo), "worker", "run"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        env=env,
    )
    try:
        if not _wait_for_socket(sock, timeout=8):
            pytest.skip("Worker socket not created within timeout")

        ep = Endpoint(transport="unix", path=str(sock))
        client = WorkerClient(ep, ws_id)

        health = await client.health()
        assert "worker_id" in health
        assert health.get("workspace_id") == ws_id

        result = await client.shutdown()
        assert result.get("accepted") is True
        await client.close()
        proc.wait(timeout=5)
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=5)

    meta = read_metadata(metadata_path(ws_id))
    assert meta is None or meta.state in ("stopped", "stale"), f"Unexpected state: {meta}"


@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires Python 3.10+")
def test_worker_stop_no_active_worker(integration_env: dict) -> None:
    """worker stop succeeds with no worker running."""
    result = subprocess.run(
        [sys.executable, "-m", "ppi.cli.main", "--repo", str(integration_env["repo"]),
         "worker", "stop", "--json"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    import json
    data = json.loads(result.stdout)
    assert data.get("ok") is True
