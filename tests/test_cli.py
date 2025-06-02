import json
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


def test_run_and_fix_with_mock_llm(tmp_path):
    traceback_sample = 'Traceback (most recent call last):\n  File "test_file.py", line 10, in test_func\n    assert x == 1'

    with (
        patch(
            "cybermule.commands.run_and_fix.run_test",
            return_value={
                "failure_count": 1,
                "tracebacks": {"test_func": traceback_sample},
            },
        ),
        patch(
            "cybermule.commands.run_and_fix.get_first_failure",
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
        mock_llm.generate.return_value = "<error_summary>This is a mock summary of the failure.</error_summary>"
        mock_get_llm.return_value = mock_llm

        runner = CliRunner()
        result = runner.invoke(
            app, ["--config=config.test.yaml", "run-and-fix", "--summarize-only"]
        )

        assert result.exit_code == 0
        assert "This is a mock summary of the failure." in result.output

def test_run_and_fix_with_mock_llm_fix_mode(tmp_path):
    traceback_sample = 'Traceback (most recent call last):\n  File "test_file.py", line 10, in test_func\n    assert x == 1'

    file_path = tmp_path / "some_file.py"
    file_path.write_text("original line\n" * 100)
    fix_plan = {
        "fix_description": "...",
        "edits": [
            {
                "file": str(file_path),
                "line_start": 42,
                "line_end": 42,
                "code_snippet": "if x == 1:"
            }
        ]
    }

    with (
        patch(
            "cybermule.commands.run_and_fix.run_test",
            return_value={
                "failure_count": 1,
                "tracebacks": {"test_func": traceback_sample},
            },
        ),
        patch(
            "cybermule.commands.run_and_fix.get_first_failure",
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
        mock_llm.generate.return_value = f"<error_summary>This is a mock summary of the failure.</error_summary>\n```json\n{json.dumps(fix_plan, indent=2)}\n```"
        mock_get_llm.return_value = mock_llm

        runner = CliRunner()
        result = runner.invoke(
            app,
            ["--config=config.test.yaml", "run-and-fix"],
        )

        # Print on failure for easier debug
        assert result.exit_code == 0, f"STDOUT:\n{result.output}\nSTDERR:\n{result.stderr}"
        lines = file_path.read_text().splitlines()
        assert len(lines) == 101 # inserted
        assert lines[42 - 1] == 'if x == 1:' # inserted "if x == 1:" at line 42

def test_run_and_fix_with_multi_edit_plan(tmp_path):
    file_a = tmp_path / "file_a.py"
    file_b = tmp_path / "file_b.py"
    file_a.write_text("x = 0\n" * 50)
    file_b.write_text("y = 0\n" * 50)

    fix_plan = {
        "fix_description": "Edit both files",
        "edits": [
            {
                "file": str(file_a),
                "line_start": 10,
                "line_end": 10,
                "code_snippet": "x = 42"
            },
            {
                "file": str(file_b),
                "line_start": 20,
                "line_end": 21,
                "code_snippet": "y = 999"
            }
        ]
    }

    with (
        patch("cybermule.commands.run_and_fix.run_test", return_value={"failure_count": 1, "tracebacks": {"test_func": "mock traceback"}}),
        patch("cybermule.commands.run_and_fix.get_first_failure", return_value=("test_func", "mock traceback")),
        patch("cybermule.executors.analyzer.get_llm_provider") as mock_get_llm,
        patch("cybermule.executors.analyzer.get_prompt_path", return_value="dummy.j2"),
        patch("cybermule.executors.analyzer.render_template", return_value="rendered"),
    ):
        mock_llm = MagicMock()
        mock_llm.generate.return_value = f"<error_summary>some error</error_summary>\n```json\n{json.dumps(fix_plan, indent=2)}\n```"
        mock_get_llm.return_value = mock_llm

        runner = CliRunner()
        result = runner.invoke(app, ["--config=config.test.yaml", "run-and-fix"])

        assert result.exit_code == 0
        assert "🧾 Fix description: Edit both files" in result.output
        assert "[apply_fix] ✅ Applied 2 edits across 2 file(s)" in result.output

def test_run_and_fix_with_test_selection(tmp_path):
    fix_plan = {
        "fix_description": "Fix for selected test",
        "edits": [
            {
                "file": str(tmp_path / "some_file.py"),
                "line_start": 5,
                "line_end": 5,
                "code_snippet": "print('inserted line')"
            }
        ]
    }

    with (
        patch("cybermule.commands.run_and_fix.run_single_test", return_value={"failure_count": 1, "tracebacks": {"test_selected": "sample traceback"}}),
        patch("cybermule.commands.run_and_fix.get_first_failure", return_value=("test_selected", "sample traceback")),
        patch("cybermule.executors.analyzer.get_llm_provider") as mock_get_llm,
        patch("cybermule.executors.analyzer.get_prompt_path", return_value="dummy.j2"),
        patch("cybermule.executors.analyzer.render_template", return_value="rendered"),
    ):
        mock_llm = MagicMock()
        mock_llm.generate.return_value = f"<error_summary>some error</error_summary>\n```json\n{json.dumps(fix_plan, indent=2)}\n```"
        mock_get_llm.return_value = mock_llm

        runner = CliRunner()
        (tmp_path / "some_file.py").write_text("print('original')\n" * 10)
        result = runner.invoke(app, ["--config=config.test.yaml", "run-and-fix", "--test", "test_selected"])

        assert result.exit_code == 0
        assert "test_selected" in result.output
