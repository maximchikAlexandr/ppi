from __future__ import annotations

import asyncio
import signal
from pathlib import Path

from ppi.worker_ipc.server import WorkerServer

from .runtime_paths import socket_path
from .worker_runtime import WorkerRuntime


def run_worker_foreground(ctx: dict) -> None:
    workspace_id = ctx["workspace_id"]
    project_path = Path(ctx["project_path"])
    analysis_path = Path(ctx["analysis_path"])
    profile = ctx.get("profile", "odoo")
    display_name = project_path.name

    runtime = WorkerRuntime(workspace_id, project_path, analysis_path, profile, display_name)

    async def _run():
        runtime.write_metadata()
        socket = socket_path(workspace_id)
        server = WorkerServer(str(socket), workspace_id)
        server.set_handle_request(runtime._handle_command)
        await server.start()

        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGTERM, runtime._shutdown_event.set)
        loop.add_signal_handler(signal.SIGINT, runtime._shutdown_event.set)

        await runtime.start()
        await runtime._shutdown_event.wait()
        await server.stop()

    asyncio.run(_run())
