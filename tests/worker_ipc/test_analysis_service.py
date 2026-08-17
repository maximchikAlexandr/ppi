from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ppi.worker_ipc.analysis_service import AnalysisService, _batch_succeeded
from ppi.worker_ipc.protocol import AnalysisStartRequest


def test_batch_without_odoo_modules_is_not_a_commit_failure() -> None:
    batch = MagicMock()
    batch.files = batch.modules = batch.edges = ()
    batch.failures = (MagicMock(error_text="No matching Odoo modules found under:\n"),)
    assert _batch_succeeded(batch)


def test_batch_with_real_failure_is_a_commit_failure() -> None:
    batch = MagicMock()
    batch.files = batch.modules = batch.edges = ()
    batch.failures = (MagicMock(error_text="simulated commit metadata failure"),)
    assert not _batch_succeeded(batch)


@pytest.mark.asyncio
async def test_run_calls_walk_history(tmp_path: Path) -> None:
    store = tmp_path / "analysis" / "history.duckdb"
    store.parent.mkdir(parents=True)
    service = AnalysisService(store, tmp_path, tmp_path / "analysis")

    mock_writer = MagicMock()
    mock_writer.get_project.return_value = None
    mock_writer.stored_commit_hashes.return_value = set()
    mock_writer.close.return_value = None

    mock_batch = MagicMock()
    mock_batch.commit.commit_hash = "abc123"
    mock_state = MagicMock()
    mock_state.commits_total = 1

    with (
        patch("ppi.worker_ipc.analysis_service.StoreWriter", return_value=mock_writer),
        patch("ppi.worker_ipc.analysis_service.walk_history") as mock_walk,
        patch("ppi.worker_ipc.analysis_service.project_lock.write_lock") as mock_lock,
        patch("ppi.worker_ipc.analysis_service.git.resolve_branch") as mock_resolve,
    ):
        mock_resolve.return_value.is_ok.return_value = True
        mock_resolve.return_value.ok = "main"
        mock_walk.return_value.is_error.return_value = False
        mock_walk.return_value.ok = ([mock_batch], mock_state)
        mock_lock.return_value.__enter__.return_value = None
        mock_lock.return_value.__exit__.return_value = None

        cancel_flag = MagicMock(return_value=False)
        progress_cb = MagicMock()

        await service.run_legacy(
            mode="incremental", cancel_flag=cancel_flag, progress_callback=progress_cb
        )


@pytest.mark.asyncio
async def test_run_records_partial_commit_failure(tmp_path: Path) -> None:
    """A failed batch remains a completed run with an accurate failed count."""
    service = AnalysisService(tmp_path / "history.duckdb", tmp_path, tmp_path / "analysis")
    writer = MagicMock()
    writer.get_project.return_value = None
    writer.close.return_value = None
    failed_batch = MagicMock()
    failed_batch.commit.commit_hash = "deadbeef00"
    failed_batch.files = failed_batch.modules = failed_batch.edges = ()
    failed_batch.failures = (MagicMock(error_text="simulated commit metadata failure"),)
    state = MagicMock(commits_total=1)

    with (
        patch("ppi.worker_ipc.analysis_service.StoreWriter", return_value=writer),
        patch("ppi.worker_ipc.analysis_service.walk_history") as walk,
        patch("ppi.worker_ipc.analysis_service.project_lock.write_lock") as lock,
        patch("ppi.worker_ipc.analysis_service.git.resolve_branch") as resolve,
    ):
        resolve.return_value.is_ok.return_value = True
        resolve.return_value.ok = "main"
        walk.return_value.is_error.return_value = False
        walk.return_value.ok = ([failed_batch], state)
        lock.return_value.__enter__.return_value = None
        lock.return_value.__exit__.return_value = None

        result = await service.run(run_id="partial", request=AnalysisStartRequest(branch="main"))

    assert result.status == "completed"
    assert result.commits_succeeded == 0
    assert result.commits_failed == 1
