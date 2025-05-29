from unittest.mock import patch
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

def test_review_commit_mock_llm(monkeypatch):
    runner = CliRunner()

    # Patch git_utils to provide fake commit data
    with patch("cybermule.commands.review_commit.git_utils.get_latest_commit_sha", return_value="abcdef1"), \
         patch("cybermule.commands.review_commit.git_utils.get_latest_commit_message", return_value="Fix bug in handler"), \
         patch("cybermule.commands.review_commit.git_utils.get_latest_commit_diff", return_value="diff --git a/app.py b/app.py\n..."):

        result = runner.invoke(app, ["review-commit"])

        assert result.exit_code == 0
        # The mock llm should echo the title and the diff which should be a part of the prompt
        assert "Fix bug in handler" in result.output
        assert "diff --git a/app.py b/app.py" in result.output
