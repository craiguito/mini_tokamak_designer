from typer.testing import CliRunner

from mini_tokamak.cli import app


def test_cli_verify_smoke():
    runner = CliRunner()
    result = runner.invoke(app, ["verify"])
    assert result.exit_code == 0
    assert "MiniTokamak Designer stack verification" in result.output


def test_cli_run_help_includes_torax_top_n():
    runner = CliRunner()
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0
    assert "--torax-top-n" in result.output
