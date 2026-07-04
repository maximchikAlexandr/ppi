"""Baseline smoke tests for documented CLI surfaces."""

from __future__ import annotations

import tempfile
from pathlib import Path

from click.testing import CliRunner

from ppi.cli.main import cli


def test_cli_help_smoke() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Analyze Git history metrics" in result.output


def _repo_flag() -> list[str]:
    return ["--repo", str(Path(tempfile.mkdtemp()))]


def test_analyze_help_smoke() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, [*_repo_flag(), "analyze", "--help"])
    assert result.exit_code == 0
    assert "Walk non-merge commit history" in result.output


def test_query_help_smoke() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, [*_repo_flag(), "query", "--help"])
    assert result.exit_code == 0


def test_serve_help_smoke() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, [*_repo_flag(), "serve", "--help"])
    assert result.exit_code == 0


def test_doctor_help_smoke() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, [*_repo_flag(), "doctor", "--help"])
    assert result.exit_code == 0


def test_rpc_help_smoke() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, [*_repo_flag(), "rpc", "--help"])
    assert result.exit_code == 0


def test_openapi_help_smoke() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, [*_repo_flag(), "openapi", "--help"])
    assert result.exit_code == 0
