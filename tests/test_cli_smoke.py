from typer.testing import CliRunner

from mini_tokamak.cli import app


def test_cli_verify_smoke():
    runner = CliRunner()
    result = runner.invoke(app, ["verify"])
    assert result.exit_code == 0
    assert "MiniTokamak Designer stack verification" in result.output

