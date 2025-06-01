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
    assert "Model response: [MOCKED] Response to: User: Say hello" in result.output


def test_review_commit_mock_llm(monkeypatch):
    runner = CliRunner()

    # Patch git_utils to provide fake commit data
    with (
        patch(
            "cybermule.commands.review_commit.git_utils.get_latest_commit_sha",
            return_value="abcdef1",
        ),
        patch(
            "cybermule.commands.review_commit.git_utils.get_commit_message_by_sha",
            return_value="Fix bug in handler",
        ),
        patch(
            "cybermule.commands.review_commit.git_utils.get_commit_diff_by_sha",
            return_value="diff --git a/app.py b/app.py\n...",
        ),
    ):

        result = runner.invoke(app, ["--config=config.test.yaml", "review-commit"])

        assert result.exit_code == 0
        assert "Fix bug in handler" in result.output
        assert "diff --git a/app.py" in result.output


def test_refactor_cli_smoke(tmp_path):
    file_to_refactor = tmp_path / "example.py"
    file_to_refactor.write_text("print('hello')\n")

    fake_response = "```python\nprint('refactored')\n```"

    with patch("cybermule.executors.run_refactor.get_llm_provider") as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = fake_response
        mock_get_llm.return_value = mock_llm

        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "--config=config.test.yaml",
                "refactor",
                str(file_to_refactor),
                "--goal=rename print statement",
                "--preview",
            ],
        )

    assert result.exit_code == 0
    assert "-print('hello')" in result.output
    assert "+print('refactored')" in result.output


def test_run_and_analyze_with_mock_llm(tmp_path):
    traceback_sample = 'Traceback (most recent call last):\n  File "test_file.py", line 10, in test_func\n    assert x == 1'

    with (
        patch(
            "cybermule.commands.run_and_analyze.run_pytest",
            return_value={
                "failure_count": 1,
                "tracebacks": {"test_func": traceback_sample},
            },
        ),
        patch(
            "cybermule.commands.run_and_analyze.get_first_failure",
            return_value=("test_func", traceback_sample),
        ),
        patch("cybermule.executors.analyzer.get_llm_provider") as mock_get_llm,
        patch(
            "cybermule.executors.analyzer.get_prompt_path",
            return_value="dummy_template.j2",
        ),
        patch(
            "cybermule.executors.analyzer.render_template",
            return_value="rendered prompt",
        ),
    ):

        mock_llm = MagicMock()
        mock_llm.generate.return_value = "This is a mock summary of the failure."
        mock_get_llm.return_value = mock_llm

        runner = CliRunner()
        result = runner.invoke(
            app, ["--config=config.test.yaml", "run-and-analyze", "--summarize"]
        )

        assert result.exit_code == 0
        assert "This is a mock summary of the failure." in result.output

def test_run_and_analyze_with_mock_llm_fix_mode(tmp_path):
    traceback_sample = 'Traceback (most recent call last):\n  File "test_file.py", line 10, in test_func\n    assert x == 1'

    with (
        patch(
            "cybermule.commands.run_and_analyze.run_pytest",
            return_value={
                "failure_count": 1,
                "tracebacks": {"test_func": traceback_sample},
            },
        ),
        patch(
            "cybermule.commands.run_and_analyze.get_first_failure",
            return_value=("test_func", traceback_sample),
        ),
        patch("cybermule.executors.analyzer.get_llm_provider") as mock_get_llm,
        patch(
            "cybermule.executors.analyzer.get_prompt_path",
            return_value="dummy_template.j2",
        ),
        patch(
            "cybermule.executors.analyzer.render_template",
            return_value="rendered prompt",
        ),
    ):
        mock_llm = MagicMock()
        mock_llm.generate.return_value = """```json
{
  "file": "some_file.py",
  "line": 42,
  "fix_description": "Replace invalid comparison",
  "code_snippet": "if x == 1:"
}
```"""
        mock_get_llm.return_value = mock_llm

        runner = CliRunner()
        result = runner.invoke(
            app,
            ["--config=config.test.yaml", "run-and-analyze", "--no-summarize"],
        )

        # Print on failure for easier debug
        assert result.exit_code == 0, f"STDOUT:\n{result.output}\nSTDERR:\n{result.stderr}"
        assert "'file': 'some_file.py'" in result.output
        assert "'line': 42" in result.output
        assert "'code_snippet': 'if x == 1:'" in result.output