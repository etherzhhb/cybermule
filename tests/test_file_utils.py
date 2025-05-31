import pytest
from pathlib import Path
from cybermule.utils.file_utils import read_file_content, resolve_context_inputs

def test_read_existing_file(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, world!")
    content = read_file_content(test_file)
    assert content == "Hello, world!"

def test_read_nonexistent_file(tmp_path):
    fake_file = tmp_path / "missing.txt"
    content = read_file_content(fake_file, verbose=False)
    assert content == ""  # Should return empty string on failure

def test_read_nonexistent_file_verbose(tmp_path, capsys):
    fake_file = tmp_path / "missing.txt"
    content = read_file_content(fake_file, verbose=True)
    captured = capsys.readouterr()
    assert "Error reading file" in captured.err
    assert content == ""

def test_resolve_context_inputs_with_glob_and_dir(tmp_path):
    # Create test structure
    (tmp_path / "subdir").mkdir()
    f1 = tmp_path / "a.py"
    f2 = tmp_path / "b.txt"
    f3 = tmp_path / "subdir" / "c.py"
    f1.write_text("# a")
    f2.write_text("# b")
    f3.write_text("# c")

    # Case: resolve .py files using dir + glob
    results = resolve_context_inputs([str(tmp_path), str(tmp_path / "subdir" / "*.py")])
    result_names = sorted(p.name for p in results)

    assert "a.py" in result_names
    assert "c.py" in result_names
    assert "b.txt" not in result_names  # should be excluded
