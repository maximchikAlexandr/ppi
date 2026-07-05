from click.testing import CliRunner

from ppi.cli.main import cli


def test_serve_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--repo", "/tmp", "serve", "--help"])
    assert result.exit_code == 0
