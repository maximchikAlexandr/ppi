"""CLI regression coverage for isolated branch analysis."""

from __future__ import annotations

import asyncio
import subprocess
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import click
import pytest
from click.testing import CliRunner

from ppi.cli.main import _analyze_via_worker, cli
from ppi.runtime.paths import store_path
from ppi.worker_ipc.protocol import AnalysisStartRequest


@dataclass
class _WorkerClient:
    requests: list[dict[str, str]]

    async def analysis_start(self, request: AnalysisStartRequest) -> dict[str, str]:
        self.requests.append({
            "mode": request.mode,
            "reason": request.reason,
            "branch": request.branch or "",
        })
        return {"state": "completed", "run_id": request.branch or ""}

    async def analysis_status(self) -> dict[str, str]:
        return {"state": "completed"}

    async def close(self) -> None:
        return None


def test_cli_delegates_requested_branches_without_touching_dirty_checkout(
    mini_repo: Path,
    tmp_path: Path,
) -> None:
    """The CLI sends concrete branch names to the worker and leaves checkout state alone."""
    subprocess.run(["git", "-C", str(mini_repo), "branch", "dev"], check=True)
    subprocess.run(["git", "-C", str(mini_repo), "switch", "-c", "feature/test"], check=True)
    dirty_file = mini_repo / "local-note.txt"
    dirty_file.write_text("do not touch\n", encoding="utf-8")
    before_branch = subprocess.check_output(
        ["git", "-C", str(mini_repo), "branch", "--show-current"], text=True,
    ).strip()
    before_status = subprocess.check_output(
        ["git", "-C", str(mini_repo), "status", "--porcelain"], text=True,
    )

    requests: list[dict[str, str]] = []
    client = _WorkerClient(requests)

    class _Gateway:
        def __init__(self, *_args: object) -> None:
            pass

        async def get_client(self, *, start_if_missing: bool) -> SimpleNamespace:
            assert start_if_missing is True
            return SimpleNamespace(status="healthy", client=client)

    runner = CliRunner()
    command_prefix = ["--repo", str(mini_repo), "--analysis-dir", str(tmp_path / "runtime")]
    with patch("ppi.cli.main.WorkerGateway", _Gateway):
        for branch in ("dev", "feature/test", "feature/test"):
            result = runner.invoke(cli, [*command_prefix, "--branch", branch, "analyze"])
            assert result.exit_code == 0, result.output

        invalid = runner.invoke(
            cli,
            [*command_prefix, "--branch", "does-not-exist", "analyze"],
        )

    assert invalid.exit_code != 0
    assert requests == [
        {"mode": "incremental", "reason": "cli", "branch": "dev"},
        {"mode": "incremental", "reason": "cli", "branch": "feature/test"},
        {"mode": "incremental", "reason": "cli", "branch": "feature/test"},
    ]
    assert not store_path(mini_repo).exists()
    assert subprocess.check_output(
        ["git", "-C", str(mini_repo), "branch", "--show-current"], text=True,
    ).strip() == before_branch
    assert subprocess.check_output(
        ["git", "-C", str(mini_repo), "status", "--porcelain"], text=True,
    ) == before_status


@pytest.mark.parametrize("state", ["failed", "cancelled"])
def test_worker_terminal_error_closes_client(state: str) -> None:
    client = _WorkerClient([])
    client.analysis_status = AsyncMock(return_value={"state": state, "message": state})
    client.close = AsyncMock()
    with pytest.raises(click.ClickException, match=state):
        asyncio.run(_analyze_via_worker(client, AnalysisStartRequest(branch="main"), False))
    client.close.assert_awaited_once()


def test_worker_timeout_closes_client() -> None:
    client = _WorkerClient([])
    client.analysis_status = AsyncMock(return_value={"state": "running"})
    client.close = AsyncMock()
    with (
        patch("ppi.cli.main.asyncio.sleep", new=AsyncMock()),
        pytest.raises(click.ClickException, match="Timed out"),
    ):
        asyncio.run(_analyze_via_worker(client, AnalysisStartRequest(branch="main"), False))
    client.close.assert_awaited_once()


def test_real_worker_switches_shared_store_without_touching_dirty_checkout(
    mini_repo: Path,
    tmp_path: Path,
) -> None:
    subprocess.run(["git", "-C", str(mini_repo), "branch", "dev"], check=True)
    subprocess.run(["git", "-C", str(mini_repo), "switch", "-c", "feature/test"], check=True)
    dirty = mini_repo / "local-note.txt"
    dirty.write_text("keep me\n", encoding="utf-8")
    before_branch = subprocess.check_output(
        ["git", "-C", str(mini_repo), "branch", "--show-current"], text=True,
    ).strip()
    before_status = subprocess.check_output(
        ["git", "-C", str(mini_repo), "status", "--porcelain"], text=True,
    )
    runtime = tmp_path / "runtime"
    prefix = ["--repo", str(mini_repo), "--analysis-dir", str(runtime)]
    runner = CliRunner()
    try:
        for branch in ("dev", "feature/test", "feature/test"):
            result = runner.invoke(cli, [*prefix, "--branch", branch, "analyze"])
            assert result.exit_code == 0, result.output
        db = store_path(mini_repo)
        before_invalid = db.read_bytes()
        invalid = runner.invoke(cli, [*prefix, "--branch", "not-a-branch", "analyze"])
        assert invalid.exit_code != 0
        assert db.read_bytes() == before_invalid
        import duckdb
        conn = duckdb.connect(str(db), read_only=True)
        try:
            assert conn.execute("SELECT branch FROM project").fetchone() == ("feature/test",)
            assert conn.execute(
                "SELECT mode FROM analysis_run ORDER BY started_at"
            ).fetchall() == [("rebuild",), ("incremental",)]
        finally:
            conn.close()
    finally:
        runner.invoke(cli, [*prefix, "worker", "stop"])
    assert subprocess.check_output(
        ["git", "-C", str(mini_repo), "branch", "--show-current"], text=True,
    ).strip() == before_branch
    assert subprocess.check_output(
        ["git", "-C", str(mini_repo), "status", "--porcelain"], text=True,
    ) == before_status
