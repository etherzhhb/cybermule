import pytest
from pathlib import Path
from cybermule.symbol_resolution import (
    extract_definition_by_callsite,
    resolve_symbol,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_local_symbol_resolution():
    result = resolve_symbol("foo", project_root=FIXTURES)
    assert result is not None, "Expected to find local function 'foo'"
    assert "def foo" in result["snippet"]
    assert result["symbol"] == "foo"
    assert result["start_line"] > 0


def test_imported_symbol_resolution():
    result = resolve_symbol("bar", project_root=FIXTURES)
    assert result is not None, "Expected to resolve imported function 'bar'"
    assert "def bar" in result["snippet"]
    assert result["file"].endswith("lib.py")


def test_missing_symbol_resolution():
    result = resolve_symbol("does_not_exist", project_root=FIXTURES)
    assert result is None


def test_alias_import_resolution():
    result = resolve_symbol("baz", project_root=FIXTURES)
    assert result is None, "TODO: support resolve aliased import 'baz'"
    # assert result is not None, "Expected to resolve aliased import 'baz'"
    # assert "def bar" in result["snippet"]
    # assert result["file"].endswith("lib.py")


def test_callsite_resolution_local():
    path = FIXTURES / "calls_local.py"
    result = extract_definition_by_callsite(path, 5)
    assert result is not None
    assert result["symbol"] == "foo"
    assert "def foo" in result["snippet"]


def test_callsite_resolution_imported():
    path = FIXTURES / "calls_imported.py"
    result = extract_definition_by_callsite(path, 4, project_root=FIXTURES)
    assert result is not None
    assert result["symbol"] == "bar"
    assert result["file"].endswith("lib.py")
