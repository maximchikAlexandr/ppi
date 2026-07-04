"""CLI compatibility tests for query output contracts."""

from __future__ import annotations

import tempfile
from pathlib import Path

from click.testing import CliRunner

from ppi.cli.main import cli


def _repo_flag() -> list[str]:
    return ["--repo", str(Path(tempfile.mkdtemp()))]


def test_query_help_returns_zero() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, [*_repo_flag(), "query", "--help"])
    assert result.exit_code == 0
