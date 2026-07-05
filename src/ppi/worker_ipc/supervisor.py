from __future__ import annotations

import asyncio
import subprocess
import sys
import time
from pathlib import Path

import msgspec
from ppi.worker_ipc.client import WorkerClient, WorkerClientError
from ppi.worker_ipc.constants import HEALTH_CHECK_TIMEOUT_SECONDS, WORKER_START_TIMEOUT_SECONDS
from ppi.worker_ipc.runtime_paths import Endpoint


class Supervisor:
    def __init__(self, repo: Path, workspace_id: str, profile: str, analysis_dir: Path) -> None:
        self._repo = repo
        self._workspace_id = workspace_id
        self._profile = profile
        self._analysis_dir = analysis_dir

    def spawn_worker(self) -> subprocess.Popen:
        cmd = [
            sys.executable,
            "-m",
            "ppi.cli.main",
            "--repo",
            str(self._repo),
            "--profile",
            self._profile,
            "--analysis-dir",
            str(self._analysis_dir),
            "worker",
            "run",
        ]
        return subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    async def wait_until_healthy(self, endpoint: Endpoint) -> bool:
        deadline = time.monotonic() + WORKER_START_TIMEOUT_SECONDS
        client = WorkerClient(endpoint, self._workspace_id)
        attempt = 0
        while time.monotonic() < deadline:
            try:
                result = await asyncio.wait_for(
                    client.health(),
                    timeout=HEALTH_CHECK_TIMEOUT_SECONDS,
                )
                if result.get("state") in ("idle", "starting"):
                    await client.close()
                    return True
            except (TimeoutError, WorkerClientError, ConnectionError, OSError, msgspec.DecodeError, msgspec.ValidationError):
                pass
            # ponytail: exponential backoff capped at 1s
            await asyncio.sleep(min(0.2 * 2**attempt, 1.0))
            attempt += 1
        await client.close()
        return False


