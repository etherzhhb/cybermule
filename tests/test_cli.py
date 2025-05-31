from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from cybermule.cli.main import app

def test_cli_help():
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output or "usage:" in result.output.lower()

def test_check_mock_llm():
    result = CliRunner().invoke(app, ["--config=config.test.yaml", "check-llm"])
    assert result.exit_code == 0
    assert "Model response: [MOCKED] Response to: Say hello" in result.output

def test_review_commit_mock_llm(monkeypatch):
    runner = CliRunner()

    # Patch git_utils to provide fake commit data
    with patch("cybermule.commands.review_commit.git_utils.get_latest_commit_sha", return_value="abcdef1"), \
         patch("cybermule.commands.review_commit.git_utils.get_commit_message", return_value="Fix bug in handler"), \
         patch("cybermule.commands.review_commit.git_utils.get_commit_diff", return_value="diff --git a/app.py b/app.py\n..."):

        result = runner.invoke(app, ["--config=config.test.yaml", "review-commit"])

        assert result.exit_code == 0
        # The mock llm should echo the title and the diff which should be a part of the prompt
        assert "Fix bug in handler" in result.output
        assert "diff --git a/app.py b/app.py" in result.output

def test_refactor_preview(tmp_path):
    file_to_refactor = tmp_path / "example.py"
    file_to_refactor.write_text("print('hello')\n")

    # Create a fake refactoring response with a code block
    fake_response = "```python\nprint('refactored')\n```"

    with patch("cybermule.commands.refactor.get_llm_provider") as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = fake_response
        mock_get_llm.return_value = mock_llm

        runner = CliRunner()
        result = runner.invoke(app, [
            "--config=config.test.yaml",
            "refactor",
            str(file_to_refactor),
            "--goal=rename print statement",
            "--preview"
        ])

    assert result.exit_code == 0
    assert "-print('hello')" in result.output
    assert "+print('refactored')" in result.output

def test_refactor_cli_with_context_glob(tmp_path):
    runner = CliRunner()

    # Create main file to refactor
    file_to_refactor = tmp_path / "main.py"
    file_to_refactor.write_text("print('Hello')\n")

    # Create context files
    (tmp_path / "ctx").mkdir()
    (tmp_path / "ctx" / "util1.py").write_text("def util(): pass")
    (tmp_path / "ctx" / "util2.py").write_text("def helper(): pass")

    # Fake LLM response with a code block
    fake_llm_response = "```python\nprint('Refactored')\n```"

    with patch("cybermule.commands.refactor.get_llm_provider") as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = fake_llm_response
        mock_get_llm.return_value = mock_llm

        result = runner.invoke(app, [
            "--config=config.test.yaml",
            "refactor",
            str(file_to_refactor),
            "--goal=Update print statement",
            "--context", str(tmp_path / "ctx"),  # use directory as context
            "--preview"
        ])

    assert result.exit_code == 0
    assert "-print('Hello')" in result.output
    assert "+print('Refactored')" in result.output
    assert "📚 Added 2 context file(s)" in result.output
