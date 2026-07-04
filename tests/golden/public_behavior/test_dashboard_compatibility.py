"""Server/dashboard compatibility tests for response shapes."""

from __future__ import annotations

import tempfile
from pathlib import Path

from click.testing import CliRunner

from ppi.cli.main import cli


def _repo_flag() -> list[str]:
    return ["--repo", str(Path(tempfile.mkdtemp()))]


def test_openapi_help_returns_zero() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, [*_repo_flag(), "openapi", "--help"])
    assert result.exit_code == 0
