
from click.testing import CliRunner

from ppi.cli.main import cli


def test_analyze_via_worker_flag_in_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--repo", "/tmp", "analyze", "--help"])
    assert result.exit_code == 0
    assert "--via-worker" in result.output
