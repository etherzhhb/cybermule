from typer.testing import CliRunner
from cybermule.cli.main import app

runner = CliRunner()

def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output or "usage:" in result.output.lower()
