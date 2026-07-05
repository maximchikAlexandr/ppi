from click.testing import CliRunner

from ppi.cli.main import cli


def test_query_via_worker_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--repo", "/tmp", "query", "--help"])
    assert result.exit_code == 0
    assert "--via-worker" in result.output
