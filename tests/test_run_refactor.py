from pathlib import Path
from unittest.mock import MagicMock, patch

from cybermule.executors import run_refactor


def test_run_refactor_preview_diff(tmp_path):
    file_path = tmp_path / "main.py"
    file_path.write_text("print('Hello')\n")

    fake_response = "```python\nprint('Hi')\n```"

    with patch("cybermule.executors.run_refactor.get_llm_provider") as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = fake_response
        mock_get_llm.return_value = mock_llm

        node_id = run_refactor.execute(
            graph=None,
            file=file_path,
            goal="Update greeting",
            preview=True,
            debug_prompt=False,
            config={}
        )

    # File should remain unchanged
    assert file_path.read_text() == "print('Hello')\n"
    assert node_id is None


def test_run_refactor_overwrite_file(tmp_path):
    file_path = tmp_path / "file.py"
    file_path.write_text("x = 1\n")

    fake_response = "```python\nx = 42\n```"

    with patch("cybermule.executors.run_refactor.get_llm_provider") as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = fake_response
        mock_get_llm.return_value = mock_llm

        node_id = run_refactor.execute(
            graph=None,
            file=file_path,
            goal="Change value",
            preview=False,
            debug_prompt=False,
            config={}
        )

    assert file_path.read_text() == "x = 42\n"
    assert node_id is None


def test_run_refactor_with_context(tmp_path):
    file_path = tmp_path / "main.py"
    file_path.write_text("print('Main')\n")

    # Context files
    ctx_dir = tmp_path / "ctx"
    ctx_dir.mkdir()
    ctx_file_1 = ctx_dir / "util1.py"
    ctx_file_2 = ctx_dir / "util2.py"
    ctx_file_1.write_text("def util(): pass")
    ctx_file_2.write_text("def helper(): pass")

    fake_response = "```python\nprint('Updated Main')\n```"

    with patch("cybermule.executors.run_refactor.get_llm_provider") as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.generate.return_value = fake_response
        mock_get_llm.return_value = mock_llm

        node_id = run_refactor.execute(
            graph=None,
            file=file_path,
            goal="Update main",
            context=[str(ctx_dir)],
            preview=True,
            debug_prompt=True,
            config={}
        )

    # File is previewed only
    assert file_path.read_text() == "print('Main')\n"
    assert node_id is None
