"""CLI compatibility tests for doctor output and exit semantics."""

from __future__ import annotations

import tempfile
from pathlib import Path

from click.testing import CliRunner

from ppi.cli.main import cli


def _repo_flag() -> list[str]:
    return ["--repo", str(Path(tempfile.mkdtemp()))]


def test_doctor_help_returns_zero() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, [*_repo_flag(), "doctor", "--help"])
    assert result.exit_code == 0
