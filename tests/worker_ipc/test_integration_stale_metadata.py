"""Integration tests: stale metadata detection and recovery (T067, T068).

Tests use the CLI commands on pre-written stale metadata, testing the
full command path without needing a real worker subprocess.
"""

import json
import subprocess
import sys
import time

import pytest

from ppi.runtime.paths import project_id_from_repo
from ppi.worker_ipc.runtime_metadata import write_metadata, RuntimeMetadata
from ppi.worker_ipc.runtime_paths import metadata_path, socket_path


@pytest.fixture
def stale_meta(integration_env: dict, monkeypatch: pytest.MonkeyPatch) -> str:
    """Write stale runtime metadata for an integration test workspace."""
    repo = integration_env["repo"]
    ws_id = project_id_from_repo(repo)
    sock = socket_path(ws_id)
    sock.parent.mkdir(parents=True, exist_ok=True)
    meta_path = metadata_path(ws_id)
    write_metadata(meta_path, RuntimeMetadata(
        workspace_id=ws_id,
        worker_id="dead-worker-001",
        pid=999999,
        endpoint=f"unix://{sock}",
        transport="unix",
        protocol_version="1.0",
        state="idle",
        started_at=time.time(),
        updated_at=time.time(),
        last_heartbeat_at=time.time(),
        last_error=None,
    ))
    return ws_id


def test_worker_status_reports_stale_with_dead_metadata(integration_env: dict, stale_meta: str) -> None:
    """worker status --json reports stale when metadata points to dead worker."""
    result = subprocess.run(
        [sys.executable, "-m", "ppi.cli.main", "--repo", str(integration_env["repo"]),
         "worker", "status", "--json"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data.get("status") in ("stale", "unavailable"), f"Expected stale/unavailable, got {data}"


def test_worker_start_after_stale_creates_new_worker(integration_env: dict, stale_meta: str) -> None:
    """worker start after stale metadata attempts to start a fresh worker.

    The start will likely fail to spawn (no real PPI store setup), but it
    must NOT crash with an unhandled exception.
    """
    result = subprocess.run(
        [sys.executable, "-m", "ppi.cli.main", "--repo", str(integration_env["repo"]),
         "worker", "start", "--json"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"worker start crashed: {result.stderr}"
