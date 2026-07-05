from __future__ import annotations

import asyncio
import os
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Awaitable

from msgspec import structs as msgspec_structs
from ppi.worker_ipc.constants import (
    HEARTBEAT_INTERVAL_SECONDS,
    PROTOCOL_VERSION,
)
from ppi.worker_ipc.events import EventHub
from ppi.worker_ipc.protocol import (
    AnalysisState,
    WorkerCommand,
    WorkerErrorCode,
    WorkerRequest,
    WorkerState,
)
from ppi.worker_ipc.query_service import QueryService
from ppi.worker_ipc.runtime_metadata import RuntimeMetadata, read_metadata, write_metadata
from ppi.worker_ipc.runtime_paths import (
    endpoint_for_workspace,
    metadata_path,
)


class WorkerRuntime:
    def __init__(
        self,
        workspace_id: str,
        project_path: Path,
        analysis_path: Path,
        profile: str,
        display_name: str,
    ) -> None:
        self.workspace_id = workspace_id
        self.project_path = project_path
        self.analysis_path = analysis_path
        self.profile = profile
        self.display_name = display_name
        self.store_path = analysis_path / "history.duckdb"
        self.worker_id = f"worker-{uuid.uuid4().hex[:12]}"
        self.state = WorkerState.starting
        self.started_at = datetime.now(UTC).isoformat()
        self._analysis_state = AnalysisState.not_started
        self._analysis_run_id: str | None = None
        self._last_run_id: str | None = None
        self._progress_percent: float | None = None
        self._analysis_message: str = "No analysis has been run yet"
        self._cancel_flag = False
        self._analysis_task: asyncio.Task | None = None
        self._heartbeat_task: asyncio.Task | None = None
        self._shutdown_event = asyncio.Event()
        self._lock = asyncio.Lock()
        self.event_hub = EventHub(workspace_id=workspace_id, worker_id=self.worker_id)
        self._metadata_path = metadata_path(workspace_id)
        self._handlers: dict[str, Callable[..., Awaitable[dict[str, Any]]]] = {
            WorkerCommand.WORKER_HEALTH: self.handle_health,
            WorkerCommand.WORKSPACE_INFO: self.handle_workspace_info,
            WorkerCommand.ANALYSIS_STATUS: self.handle_analysis_status,
            WorkerCommand.ANALYSIS_START: self.handle_analysis_start,
            WorkerCommand.ANALYSIS_CANCEL: self.handle_analysis_cancel,
            WorkerCommand.QUERY_EXECUTE: self.handle_query_execute,
            WorkerCommand.WORKER_SHUTDOWN: self.handle_shutdown,
            WorkerCommand.EVENTS_SUBSCRIBE: self.handle_events_subscribe,
        }

    def write_metadata(self) -> None:
        ep = endpoint_for_workspace(self.workspace_id)
        meta = RuntimeMetadata(
            workspace_id=self.workspace_id,
            worker_id=self.worker_id,
            pid=os.getpid(),
            endpoint=ep.uri(),
            transport="unix",
            protocol_version=PROTOCOL_VERSION,
            state=self.state.value,
            started_at=self.started_at,
            updated_at=datetime.now(UTC).isoformat(),
            last_heartbeat_at=datetime.now(UTC).isoformat(),
        )
        write_metadata(self._metadata_path, meta)

    def _write_metadata_state(self) -> None:
        meta = read_metadata(self._metadata_path)
        if meta is not None:
            now = datetime.now(UTC).isoformat()
            meta = msgspec_structs.replace(meta, state=self.state.value, updated_at=now, last_heartbeat_at=now)
            write_metadata(self._metadata_path, meta)

    async def _update_metadata_state(self) -> None:
        async with self._lock:
            self._write_metadata_state()

    async def _finish_analysis(
        self, state: AnalysisState, event_type: str, run_id: str, message: str, code: str | None = None,
    ) -> None:
        payload: dict[str, Any] = {"run_id": run_id, "message": message}
        if code is not None:
            payload["code"] = code
        async with self._lock:
            self._analysis_state = state
            self._analysis_message = message
            self._last_run_id = run_id
            self.state = WorkerState.idle
            if state == AnalysisState.completed:
                self._progress_percent = 100.0
            await self.event_hub.emit(event_type, payload)
            self._write_metadata_state()

    async def _heartbeat_loop(self) -> None:
        while not self._shutdown_event.is_set():
            await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
            await self._update_metadata_state()

    async def start(self) -> None:
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._heartbeat_task.add_done_callback(lambda t: t.cancelled() or t.exception())
        self.state = WorkerState.idle
        await self._update_metadata_state()
        await self.event_hub.emit("worker.ready", {"state": "idle"})

    async def shutdown(self, reason: str = "user requested stop") -> dict[str, Any]:
        async with self._lock:
            if self.state == WorkerState.busy:
                return {
                    "accepted": False,
                    "error_code": WorkerErrorCode.WORKER_BUSY.value,
                    "message": "Worker is running analysis and cannot shut down safely",
                }
            self.state = WorkerState.stopping
            self._write_metadata_state()
        self._shutdown_event.set()
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
        if self._analysis_task is not None and not self._analysis_task.done():
            self._analysis_task.cancel()
        self.state = WorkerState.stopped
        await self._update_metadata_state()
        return {"accepted": True, "message": "Worker shutdown accepted"}

    async def handle_health(self, req: Any = None) -> dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "workspace_id": self.workspace_id,
            "protocol_version": PROTOCOL_VERSION,
            "state": self.state.value,
            "started_at": self.started_at,
        }

    async def handle_workspace_info(self, req: Any = None) -> dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "project_path": str(self.project_path),
            "analysis_path": str(self.analysis_path),
            "profile": self.profile,
            "display_name": self.display_name,
        }

    async def handle_analysis_status(self, req: Any = None) -> dict[str, Any]:
        return {
            "state": self._analysis_state.value,
            "current_run_id": self._analysis_run_id if self._analysis_task is not None and not self._analysis_task.done() else None,
            "last_run_id": self._last_run_id,
            "progress_percent": self._progress_percent,
            "message": self._analysis_message,
        }

    async def handle_analysis_start(self, req: Any) -> dict[str, Any]:
        payload = req.payload
        mode = payload.get("mode", "incremental")

        async with self._lock:
            if self._analysis_task is not None and not self._analysis_task.done():
                return {
                    "run_id": self._analysis_run_id,
                    "accepted": True,
                    "state": "already_running",
                    "message": "Analysis is already running",
                }

            run_id = f"run-{uuid.uuid4().hex[:12]}"
            self._analysis_run_id = run_id
            self._analysis_state = AnalysisState.running
            self._analysis_message = "Analysis started"
            self._cancel_flag = False
            self.state = WorkerState.busy
            self._write_metadata_state()

            from ppi.worker_ipc.analysis_service import AnalysisService

            analysis = AnalysisService(self.store_path, self.project_path, self.analysis_path, self.profile)

            async def _run_and_finish():
                try:
                    await analysis.run(
                        mode=mode,
                        cancel_flag=lambda: self._cancel_flag,
                        progress_callback=lambda pct, msg: self._progress_callback(run_id, pct, msg),
                    )
                    if self._cancel_flag:
                        await self._finish_analysis(AnalysisState.cancelled, "analysis.cancelled", run_id, "Analysis cancelled")
                    else:
                        await self._finish_analysis(AnalysisState.completed, "analysis.completed", run_id, "Analysis completed")
                except asyncio.CancelledError:
                    await self._finish_analysis(AnalysisState.cancelled, "analysis.cancelled", run_id, "Analysis cancelled")
                except Exception as exc:
                    await self._finish_analysis(AnalysisState.failed, "analysis.failed", run_id, str(exc), code="INTERNAL_ERROR")

            self._analysis_task = asyncio.create_task(_run_and_finish())
            await self.event_hub.emit("analysis.started", {"run_id": run_id, "mode": mode})
            return {
                "run_id": run_id,
                "accepted": True,
                "state": "running",
                "message": "Analysis started",
            }

    async def handle_analysis_cancel(self, req: Any) -> dict[str, Any]:
        async with self._lock:
            if self._analysis_task is None or self._analysis_task.done():
                return {
                    "accepted": False,
                    "run_id": None,
                    "message": "No active analysis to cancel",
                }
            self._cancel_flag = True
            return {
                "accepted": True,
                "run_id": self._analysis_run_id,
                "message": "Cancellation requested",
            }

    def _progress_callback(self, run_id: str, progress_percent: float, message: str) -> None:
        self._progress_percent = progress_percent
        self._analysis_message = message
        task = asyncio.create_task(
            self.event_hub.emit("analysis.progress", {
                "run_id": run_id,
                "progress_percent": progress_percent,
                "message": message,
            })
        )
        task.add_done_callback(lambda t: t.exception() if not t.cancelled() else None)

    async def handle_query_execute(self, req: Any) -> dict[str, Any]:
        payload = req.payload
        async with self._lock:
            if self.state == WorkerState.busy:
                return {
                    "error_code": WorkerErrorCode.WORKER_BUSY.value,
                    "message": "Worker is busy running analysis",
                }
        query_name = payload.get("query_name", "")
        parameters = payload.get("parameters", {})
        limit = payload.get("limit")
        query_service = QueryService(self.store_path)
        result = await query_service.execute(query_name, parameters, limit)
        return result

    async def _handle_command(self, req: WorkerRequest) -> dict[str, Any]:
        handler = self._handlers.get(req.command)
        if handler is None:
            return {"error_code": WorkerErrorCode.UNKNOWN_COMMAND.value, "message": f"Unknown command: {req.command}"}
        return await handler(req)

    async def handle_shutdown(self, req: Any) -> dict[str, Any]:
        reason = req.payload.get("reason", "user requested stop")
        return await self.shutdown(reason=reason)

    async def handle_events_subscribe(self, req: Any) -> dict[str, Any]:
        payload = req.payload
        event_types = payload.get("event_types")
        sub_id = await self.event_hub.subscribe(event_types)
        return {"subscription_id": sub_id, "accepted_event_types": event_types}


