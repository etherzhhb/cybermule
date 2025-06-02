# test_context_extract.py
import pytest
from pathlib import Path
from textwrap import dedent
from cybermule.utils import context_extract


def test_extract_locations_simple():
    tb = '''Traceback (most recent call last):
  File "/project/main.py", line 10, in <module>
  File "/project/module.py", line 42, in my_function
'''
    x = context_extract.extract_locations(tb)
    print(x)
    assert x[0] == {"file": "/project/main.py", "line": 10, "function": "<module>"}
    assert x[1] == {"file": "/project/module.py", "line": 42, "function": "my_function"}


def test_extract_function_at_line_found(tmp_path):
    source = dedent("""
        class MyClass:
            def method(self):
                x = 1
                return x

        def helper():
            return 42
    """)
    test_file = tmp_path / "test_code.py"
    test_file.write_text(source)

    result = context_extract.extract_function_at_line(test_file, line_number=3)
    assert result is not None
    assert result["symbol"] == "MyClass.method"
    assert "def method" in result["snippet"]
    assert result["traceback_line"] == 3
    assert result["start_line"] == 3


def test_extract_function_at_line_not_found(tmp_path):
    source = "x = 1\ny = 2\n"
    test_file = tmp_path / "test_code.py"
    test_file.write_text(source)

    result = context_extract.extract_function_at_line(test_file, line_number=1)
    assert result is None


def test_get_context_snippets_with_function_match(tmp_path):
    source = dedent("""
        def outer():
            def inner():
                return 123
            return inner()
    """)
    path = tmp_path / "nested.py"
    path.write_text(source)

    locations = [{"file": str(path), "line": 3, "function": "inner"}]
    context = context_extract.get_context_snippets(locations)

    assert str(path) in context
    assert context[str(path)]["symbol"] == "outer.inner"
    assert "def inner" in context[str(path)]["snippet"]


def test_get_context_snippets_fallback(tmp_path):
    source = "a = 1\nb = 2\nc = 3\nd = 4\ne = 5\nf = 6\n"
    path = tmp_path / "flat.py"
    path.write_text(source)

    locations = [{"file": str(path), "line": 3, "function": "irrelevant"}]
    context = context_extract.get_context_snippets(locations, fallback_window=2)

    assert str(path) in context
    snippet = context[str(path)]["snippet"]
    assert "b = 2" in snippet
    assert "c = 3" in snippet
    assert "d = 4" in snippet
    assert context[str(path)]["symbol"] is None
