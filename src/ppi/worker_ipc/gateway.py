from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from ppi.runtime.lock import LockBusyError, write_lock as worker_startup_lock
from ppi.runtime.paths import analysis_dir_for_repo, project_id_from_repo
from ppi.worker_ipc.client import WorkerClient, WorkerClientError
from ppi.worker_ipc.constants import HEALTH_CHECK_TIMEOUT_SECONDS, PROTOCOL_MAJOR
from ppi.worker_ipc.protocol import protocol_major
from ppi.worker_ipc.registry import register_or_update_from_repo
from ppi.worker_ipc.runtime_metadata import RuntimeMetadata, mark_stale, read_metadata
from ppi.worker_ipc.runtime_paths import (
    Endpoint,
    endpoint_for_workspace,
    metadata_path,
    socket_path,
    startup_lock_path,
)
from ppi.worker_ipc.supervisor import Supervisor

ClientResult = tuple[WorkerClient | None, dict[str, Any]]


class WorkerGateway:
    def __init__(self, repo: Path, profile: str = "odoo", analysis_dir: Path | None = None) -> None:
        self._repo = repo.resolve()
        self._profile = profile
        self._analysis_dir = analysis_dir or analysis_dir_for_repo(self._repo)
        self._workspace_id = project_id_from_repo(self._repo)
        self._endpoint = endpoint_for_workspace(self._workspace_id)

    async def _try_connect(self) -> ClientResult | None:
        meta = read_metadata(metadata_path(self._workspace_id))
        if meta is None:
            return None
        ep = Endpoint(transport="unix", path=socket_path(self._workspace_id).as_posix())
        client = WorkerClient(ep, self._workspace_id)
        info = await self._health_check(client, meta)
        if info["status"] == "healthy":
            return (client, info)
        await client.close()
        return None

    async def get_client(self, start_if_missing: bool = False) -> ClientResult:
        meta = read_metadata(metadata_path(self._workspace_id))

        result = await self._try_connect()
        if result is not None:
            return result

        if meta is not None and not start_if_missing:
            mark_stale(metadata_path(self._workspace_id))
            stale_ep = endpoint_for_workspace(self._workspace_id)
            return (WorkerClient(stale_ep, self._workspace_id), {
                "status": "stale",
                "message": f"Worker pid {meta.pid} is not responding",
                "details": {"pid": meta.pid, "worker_id": meta.worker_id},
            })

        if not start_if_missing:
            return (None, {
                "status": "unavailable",
                "message": "No runtime metadata found, worker not started",
            })

        lock_file = startup_lock_path(self._workspace_id)
        for _ in range(6):
            try:
                with worker_startup_lock(lock_file):
                    result = await self._try_connect()
                    if result is not None:
                        return result
                    if meta is not None:
                        mark_stale(metadata_path(self._workspace_id))

                    register_or_update_from_repo(self._repo, self._analysis_dir, self._profile)

                    supervisor = Supervisor(self._repo, self._workspace_id, self._profile, self._analysis_dir)
                    proc = supervisor.spawn_worker()

                    if not await supervisor.wait_until_healthy(self._endpoint):
                        try:
                            proc.kill()
                        except OSError:
                            pass
                        await asyncio.get_running_loop().run_in_executor(None, proc.wait)
                        return (None, {
                            "status": "unavailable",
                            "message": "Worker failed to become healthy within timeout",
                        })

                    client = WorkerClient(self._endpoint, self._workspace_id)
                    return (client, {
                        "status": "healthy",
                        "worker_id": None,
                        "message": "Worker started successfully",
                    })
            except LockBusyError:
                result = await self._try_connect()
                if result is not None:
                    return result
                await asyncio.sleep(1)
        return (None, {
            "status": "unavailable",
            "message": "Failed to acquire startup lock and no healthy worker found after retries",
        })

    async def _health_check(self, client: WorkerClient, meta: RuntimeMetadata) -> dict[str, Any]:
        try:
            health = await asyncio.wait_for(client.health(), timeout=HEALTH_CHECK_TIMEOUT_SECONDS)
        except (TimeoutError, WorkerClientError, ConnectionError, OSError):
            return {
                "status": "stale",
                "message": "Worker health check failed",
                "details": {"pid": meta.pid},
            }

        try:
            if health.get("workspace_id") != self._workspace_id:
                return {
                    "status": "workspace_mismatch",
                    "message": f"Workspace mismatch: expected {self._workspace_id}, got {health.get('workspace_id')}",
                    "details": {"expected": self._workspace_id, "got": health.get("workspace_id")},
                }

            proto = health.get("protocol_version", "")
            if proto and protocol_major(proto) != PROTOCOL_MAJOR:
                return {
                    "status": "incompatible_protocol",
                    "message": f"Protocol version mismatch: {proto}",
                    "details": {"protocol_version": proto, "expected_major": PROTOCOL_MAJOR},
                }
        except Exception:
            return {
                "status": "stale",
                "message": "Malformed health response",
                "details": {"pid": meta.pid},
            }

        return {
            "status": "healthy",
            "worker_id": health.get("worker_id"),
            "message": "Worker is healthy",
        }
