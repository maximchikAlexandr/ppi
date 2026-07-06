"""Doctor worker runtime checks (R-026).

Verifies that the ``doctor`` Click command emits the worker_runtime
checks for a real (empty) repository.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from ppi.cli.main import CliContext, cli


def _git_init(path: Path) -> None:
    subprocess.run(["git", "init", "--initial-branch=main", str(path)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "config", "user.email", "t@e"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "config", "user.name", "t"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "commit", "--allow-empty", "-m", "init"], check=True, capture_output=True)


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init(repo)
    return repo


def _make_ctx(repo: Path, analysis_dir: Path) -> CliContext:
    return CliContext(
        repo=repo,
        branch=None,
        profile="odoo",
        analysis_dir=analysis_dir,
        verbose=False,
    )


def test_doctor_reports_worker_registry(git_repo: Path, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PPI_WORKSPACE_REGISTRY", str(tmp_path / "registry.json"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "xdg"))
    analysis_dir = tmp_path / "analysis"
    analysis_dir.mkdir()

    runner = CliRunner()
    result = runner.invoke(cli, ["--repo", str(git_repo), "doctor"], obj=_make_ctx(git_repo, analysis_dir))
    assert result.exit_code == 0, result.output
    assert "worker_registry" in result.output


def test_doctor_reports_worker_metadata_unavailable(git_repo: Path, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PPI_WORKSPACE_REGISTRY", str(tmp_path / "registry.json"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "xdg"))
    analysis_dir = tmp_path / "analysis"
    analysis_dir.mkdir()

    runner = CliRunner()
    result = runner.invoke(cli, ["--repo", str(git_repo), "doctor"], obj=_make_ctx(git_repo, analysis_dir))
    assert result.exit_code == 0, result.output
    assert "worker_metadata" in result.output
    assert "unavailable" in result.output


def test_doctor_reports_worker_socket_missing(git_repo: Path, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PPI_WORKSPACE_REGISTRY", str(tmp_path / "registry.json"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "xdg"))
    analysis_dir = tmp_path / "analysis"
    analysis_dir.mkdir()

    runner = CliRunner()
    result = runner.invoke(cli, ["--repo", str(git_repo), "doctor"], obj=_make_ctx(git_repo, analysis_dir))
    assert result.exit_code == 0, result.output
    assert "worker_socket" in result.output


def test_doctor_reports_worker_startup_lock_free(git_repo: Path, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PPI_WORKSPACE_REGISTRY", str(tmp_path / "registry.json"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "xdg"))
    analysis_dir = tmp_path / "analysis"
    analysis_dir.mkdir()

    runner = CliRunner()
    result = runner.invoke(cli, ["--repo", str(git_repo), "doctor"], obj=_make_ctx(git_repo, analysis_dir))
    assert result.exit_code == 0, result.output
    assert "worker_startup_lock" in result.output
    assert "free" in result.output
