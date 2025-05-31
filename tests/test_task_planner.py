from pathlib import Path
from unittest.mock import patch
from cybermule.utils.task_planner import plan_generate_or_refactor


def test_generate_task_plan():
    with patch("typer.prompt") as mock_prompt, patch("typer.confirm", return_value=True):
        mock_prompt.side_effect = [
            "generate",                   # task type
            "Generate a CLI for upload", # goal
            "generated_cli.py",          # target file
            ""  # empty context input
        ]

        plan = plan_generate_or_refactor()

    assert plan["mode"] == "generate"
    assert plan["goal"] == "Generate a CLI for upload"
    assert plan["file"] == Path("generated_cli.py")
    assert plan["context"] == []


def test_generate_with_context():
    with patch("typer.prompt") as mock_prompt, patch("typer.confirm") as mock_confirm:
        mock_prompt.side_effect = [
            "generate",
            "Generate something complex",
            "generated.py",
            "context1.py context2.py"
        ]
        mock_confirm.side_effect = [True, True]  # confirm context + confirm final plan

        plan = plan_generate_or_refactor()

    assert plan["mode"] == "generate"
    assert plan["goal"] == "Generate something complex"
    assert plan["file"] == Path("generated.py")
    assert plan["context"] == ["context1.py", "context2.py"]


def test_refactor_task_plan(tmp_path):
    file_to_refactor = tmp_path / "example.py"
    file_to_refactor.write_text("print('hello')")

    with patch("typer.prompt") as mock_prompt, patch("typer.confirm", return_value=True):
        mock_prompt.side_effect = [
            "refactor",
            str(file_to_refactor),
            "Rename print to log",
            ""  # empty context input
        ]

        plan = plan_generate_or_refactor()

    assert plan["mode"] == "refactor"
    assert plan["goal"] == "Rename print to log"
    assert plan["file"] == file_to_refactor
    assert plan["context"] == []
