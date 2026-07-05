"""Contract test: every required command in contracts/protocol.md is present in WorkerRuntime dispatch table."""

from ppi.worker_ipc.protocol import WorkerCommand
from ppi.worker_ipc.worker_runtime import WorkerRuntime


def test_all_required_commands_have_handlers(tmp_path) -> None:
    runtime = WorkerRuntime(
        workspace_id="ws-1",
        project_path=tmp_path / "project",
        analysis_path=tmp_path / "analysis",
        profile="odoo",
        display_name="project",
    )

    required_commands = {
        WorkerCommand.WORKER_HEALTH,
        WorkerCommand.WORKSPACE_INFO,
        WorkerCommand.ANALYSIS_STATUS,
        WorkerCommand.ANALYSIS_START,
        WorkerCommand.ANALYSIS_CANCEL,
        WorkerCommand.QUERY_EXECUTE,
        WorkerCommand.WORKER_SHUTDOWN,
        WorkerCommand.EVENTS_SUBSCRIBE,
    }

    for cmd in required_commands:
        handler = runtime._handlers.get(cmd)
        assert handler is not None, f"Missing handler for {cmd}"
