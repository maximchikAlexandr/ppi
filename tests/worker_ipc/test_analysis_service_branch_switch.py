"""Regression coverage for worker-owned branch analysis."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from ppi.runtime.paths import project_id_from_repo, store_path
from ppi.worker_ipc.analysis_service import AnalysisRunResult, AnalysisService
from ppi.worker_ipc.protocol import AnalysisRequestMode, AnalysisStartRequest
from ppi.worker_ipc.worker_runtime import WorkerRuntime


class _Request:
    def __init__(self, payload: dict[str, str]) -> None:
        self.payload = payload


class _CapturingAnalysisService:
    def __init__(self) -> None:
        self.branches: list[str] = []

    async def run(
        self,
        run_id: str,
        *,
        request: AnalysisStartRequest,
        **_: object,
    ) -> AnalysisRunResult:
        self.branches.append(request.branch or "")
        return AnalysisRunResult(run_id, "completed", 0, 0, 0)


@pytest.mark.asyncio
async def test_worker_uses_requested_branch_and_repository_store(tmp_path: Path) -> None:
    """The request branch must not be replaced with the worker checkout branch."""
    project = tmp_path / "project"
    service = _CapturingAnalysisService()
    runtime = WorkerRuntime(
        workspace_id="ws-branch",
        project_path=project,
        analysis_path=tmp_path / "runtime",
        profile="odoo",
        display_name="project",
        analysis_service=service,
    )

    response = await runtime.handle_analysis_start(
        _Request({"mode": "incremental", "branch": "feature/requested"}),
    )
    assert response.accepted is True
    await runtime._analysis_task

    assert service.branches == ["feature/requested"]
    assert runtime.store_path == store_path(project)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("stored_branch", "expect_rebuild", "expected_skip_commits"),
    [
        ("dev", True, set()),
        ("feature/requested", False, {"already-analyzed"}),
    ],
)
async def test_service_rebuilds_only_when_requested_branch_changes(
    tmp_path: Path,
    stored_branch: str,
    expect_rebuild: bool,
    expected_skip_commits: set[str],
) -> None:
    """A branch switch rebuilds the one shared store; same branch stays incremental."""
    project = tmp_path / "project"
    service = AnalysisService(store_path(project), project, tmp_path / "runtime")
    writer = MagicMock()
    writer.get_project.return_value = SimpleNamespace(
        project_id=project_id_from_repo(project),
        branch=stored_branch,
        scope=None,
    )
    writer.stored_commit_hashes.return_value = {"already-analyzed"}
    prepared = MagicMock()
    prepared.is_error.return_value = False
    prepared.ok = ([], SimpleNamespace(commits_total=0))
    resolved = MagicMock()
    resolved.is_ok.return_value = True
    resolved.ok = "feature/requested"

    with (
        patch("ppi.worker_ipc.analysis_service.StoreWriter", return_value=writer),
        patch(
            "ppi.worker_ipc.analysis_service.git.resolve_branch",
            return_value=resolved,
        ) as resolve,
        patch("ppi.worker_ipc.analysis_service.project_lock.write_lock"),
        patch("ppi.worker_ipc.analysis_service.walk_history", return_value=prepared) as walk,
        patch("ppi.worker_ipc.analysis_service.cleanup_worktree") as cleanup,
    ):
        result = await service.run(
            run_id="run-branch-switch",
            request=AnalysisStartRequest(branch="feature/requested"),
        )

    assert result.status == "completed"
    assert result.mode == ("rebuild" if expect_rebuild else "incremental")
    resolve.assert_called_once_with(project, "feature/requested")
    assert writer.clear_project_data.called is expect_rebuild
    assert walk.call_args.kwargs["skip_commits"] == expected_skip_commits
    cleanup.assert_called_once_with(project, tmp_path / "runtime")


@pytest.mark.asyncio
async def test_writer_lock_covers_rebuild_finish_and_close(tmp_path: Path) -> None:
    project = tmp_path / "project"
    service = AnalysisService(store_path(project), project, tmp_path / "runtime")
    writer = MagicMock()
    prepared = MagicMock()
    prepared.is_error.return_value = False
    prepared.ok = ([], SimpleNamespace(commits_total=0))
    resolved = MagicMock()
    resolved.is_ok.return_value = True
    resolved.ok = "feature/requested"
    active = 0
    operations: list[str] = []

    @contextmanager
    def lock(_path: Path):
        nonlocal active
        active += 1
        try:
            yield
        finally:
            active -= 1

    def record(name: str):
        def wrapped(*_args: object, **_kwargs: object) -> None:
            assert active == 1
            operations.append(name)

        return wrapped

    writer.clear_project_data.side_effect = record("clear")
    writer.upsert_project.side_effect = record("upsert")
    writer.start_run.side_effect = record("start")
    writer.finish_run.side_effect = record("finish")
    writer.close.side_effect = record("close")

    with (
        patch("ppi.worker_ipc.analysis_service.StoreWriter", return_value=writer) as create,
        patch("ppi.worker_ipc.analysis_service.project_lock.write_lock", lock),
        patch("ppi.worker_ipc.analysis_service.git.resolve_branch", return_value=resolved),
        patch("ppi.worker_ipc.analysis_service.walk_history", return_value=prepared),
        patch("ppi.worker_ipc.analysis_service.cleanup_worktree") as cleanup,
    ):
        result = await service.run(
            run_id="rebuild",
            request=AnalysisStartRequest(
                mode=AnalysisRequestMode.FULL,
                branch="feature/requested",
            ),
        )

    assert result.status == "completed"
    assert operations == ["clear", "upsert", "start", "finish", "close"]
    assert create.call_count == 1
    cleanup.assert_called_once_with(project, tmp_path / "runtime")


@pytest.mark.asyncio
async def test_writer_lock_covers_terminal_error_cleanup_and_close(tmp_path: Path) -> None:
    """The failure terminal write and owned cleanup share the original lock."""
    project = tmp_path / "project"
    service = AnalysisService(store_path(project), project, tmp_path / "runtime")
    writer = MagicMock()
    resolved = MagicMock()
    resolved.is_ok.return_value = True
    resolved.ok = "feature/requested"
    prepared = MagicMock()
    prepared.is_error.return_value = False
    prepared.ok = (
        iter(
            [
                MagicMock(
                    commit=SimpleNamespace(commit_hash="a" * 40),
                    files=(),
                    modules=(),
                    edges=(),
                    failures=(),
                )
            ]
        ),
        SimpleNamespace(commits_total=1),
    )
    active = 0
    enters = exits = 0

    @contextmanager
    def lock(_path: Path):
        nonlocal active, enters, exits
        enters += 1
        active += 1
        try:
            yield
        finally:
            active -= 1
            exits += 1

    writer.write_batch.side_effect = RuntimeError("batch failure")
    for method in (writer.finish_run, writer.close):
        method.side_effect = lambda *_args, **_kwargs: assert_active()

    def assert_active() -> None:
        assert active == 1

    with (
        patch("ppi.worker_ipc.analysis_service.StoreWriter", return_value=writer),
        patch("ppi.worker_ipc.analysis_service.project_lock.write_lock", lock),
        patch("ppi.worker_ipc.analysis_service.git.resolve_branch", return_value=resolved),
        patch("ppi.worker_ipc.analysis_service.walk_history", return_value=prepared),
        patch(
            "ppi.worker_ipc.analysis_service.cleanup_worktree",
            side_effect=lambda *_: assert_active(),
        ),
    ):
        result = await service.run(
            run_id="failure", request=AnalysisStartRequest(branch="feature/requested")
        )

    assert result.status == "failed"
    assert enters == exits == 1
