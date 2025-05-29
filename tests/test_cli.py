from typer.testing import CliRunner
from cybermule.cli.main import app

def test_cli_help():
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output or "usage:" in result.output.lower()

def test_check_mock_llm():
    result = CliRunner().invoke(app, ["check-llm"])
    assert result.exit_code == 0
    assert "Model response: [MOCKED] Response to: Say hello" in result.output
