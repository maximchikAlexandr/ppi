
from click.testing import CliRunner

from ppi.cli.main import cli


def test_cli_worker_group_visible() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--repo", "/tmp", "worker", "--help"])
    assert result.exit_code == 0
    assert "Manage workspace worker processes" in result.output


def test_cli_worker_run_hidden() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--repo", "/tmp", "worker", "run", "--help"])
    assert result.exit_code == 0


def test_worker_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--repo", "/tmp", "worker", "--help"])
    assert result.exit_code == 0
