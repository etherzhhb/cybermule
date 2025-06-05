import json
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from cybermule.cli.main import app


def test_cli_help():
    result = CliRunner().invoke(app, ["--help"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "Usage" in result.output or "usage:" in result.output.lower()


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
            app, ["--config=config.yaml", "run-and-fix", "--summarize-only"],
            catch_exceptions=False
        )

        assert result.exit_code == 0
        assert "This is a mock summary of the failure." in result.output

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
        patch("cybermule.executors.apply_code_change.apply_with_aider", return_value=True),
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
        result = runner.invoke(app, ["--config=config.yaml", "run-and-fix"], catch_exceptions=False)

        assert result.exit_code == 0
        assert "🧾 Fix description: Edit both files" in result.output
        assert "[apply_code_change] ✅ Fix applied using Aider to 2 file(s)." in result.output

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
        result = runner.invoke(app, ["--config=config.yaml", "run-and-fix", "--test", "test_selected"], catch_exceptions=False)

        assert result.exit_code == 0
        assert "test_selected" in result.output

def test_run_and_fix_smoke_review_commit(monkeypatch):
    runner = CliRunner()

    # Patch Git utils
    with (
        patch("cybermule.executors.git_review.git_utils.get_latest_commit_sha", return_value="abcdef1"),
        patch("cybermule.executors.git_review.git_utils.get_commit_message_by_sha", return_value="Fix bug"),
        patch("cybermule.executors.git_review.git_utils.get_commit_diff_by_sha", return_value="diff --git a/x.py b/x.py"),
        patch("cybermule.executors.analyzer.get_llm_provider") as mock_analyzer_llm,
        patch("cybermule.commands.run_and_fix.run_test", return_value=(1, "Traceback (most recent call last)...\nAssertionError")),
        patch("cybermule.tools.test_runner.get_first_failure", return_value="tests/test_x.py::test_fail"),
    ):
        mock_analyzer_llm.return_value.generate.return_value = "<error_summary>This commit introduces a bug.</error_summary>"

        result = runner.invoke(app, [
                "--config=config.yaml",
                "run-and-fix",
                "--review-commit",
                "--summarize-only"
            ],    
            catch_exceptions=False)

        assert result.exit_code == 0
        assert "Reviewing latest commit..." in result.output
        assert "Running pytest..." in result.output
        assert "This commit introduces a bug." in result.output

def test_review_commit_smoke(monkeypatch):
    runner = CliRunner()

    with (
        patch("cybermule.executors.git_review.git_utils.get_latest_commit_sha", return_value="deadbeef"),
        patch("cybermule.executors.git_review.git_utils.get_commit_message_by_sha", return_value="Add new endpoint"),
        patch("cybermule.executors.git_review.git_utils.get_commit_diff_by_sha", return_value="diff --git a/api.py b/api.py"),
        patch("cybermule.executors.git_review.get_llm_provider") as mock_llm,
    ):
        mock_llm.return_value.generate.return_value = "This looks good overall."

        result = runner.invoke(app, [
            "--config=config.yaml",
            "review-commit",
        ], catch_exceptions=False)

        assert result.exit_code == 0
        assert "Commit SHA:" in result.output
        assert "AI Review" in result.output
        assert "This looks good overall." in result.output
