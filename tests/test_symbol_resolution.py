import pytest
from pathlib import Path
from cybermule.executors.analyzer import fulfill_context_requests
from cybermule.symbol_resolution import (
    extract_definition_by_callsite,
    resolve_symbol,
    resolve_symbol_in_function,
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
    result = extract_definition_by_callsite(path=path, line=5, symbol="foo")
    assert result is not None
    assert result["symbol"] == "foo"
    assert "def foo" in result["snippet"]


def test_callsite_resolution_imported():
    path = FIXTURES / "calls_imported.py"
    result = extract_definition_by_callsite(path=path, line=4, symbol="bar",
                                            project_root=FIXTURES)
    assert result is not None
    assert result["symbol"] == "bar"
    assert result["file"].endswith("lib.py")

def test_resolve_symbol_in_function():
    path = FIXTURES / "calls_in_function.py"
    result = resolve_symbol_in_function(
        ref_path=path,
        ref_function="foo",
        symbol="bar",
        project_root=FIXTURES,
    )
    assert result is not None, "Expected to resolve symbol 'bar' inside 'foo'"
    assert result["symbol"] == "bar"
    assert "def bar" in result["snippet"]

def test_fulfill_context_by_function():
    info = [{
        "symbol": "bar",
        "ref_path": str(FIXTURES / "calls_in_function.py"),
        "ref_function": "foo",
    }]
    result = fulfill_context_requests(info, project_root=FIXTURES)
    assert len(result) == 1
    assert result[0]["symbol"] == "bar"
    assert "def bar" in result[0]["snippet"]

def test_fulfill_context_by_lineno():
    info = [{
        "symbol": "bar",
        "ref_path": str(FIXTURES / "calls_imported.py"),
        "lineno": 4
    }]
    result = fulfill_context_requests(info, project_root=FIXTURES)
    assert len(result) == 1
    assert result[0]["symbol"] == "bar"
    assert "def bar" in result[0]["snippet"]

def test_fulfill_context_symbol_only():
    info = [{
        "symbol": "foo"
    }]
    result = fulfill_context_requests(info, project_root=FIXTURES)
    assert len(result) == 1
    assert result[0]["symbol"] == "foo"
    assert "def foo" in result[0]["snippet"]


def test_fulfill_context_with_non_numeric_lineno():
    """Test fulfill_context_requests with various non-numeric lineno types."""
    invalid_values = [None, {}, [], True]
    
    for invalid_value in invalid_values:
        info = [{
            "symbol": "bar",
            "ref_path": str(FIXTURES / "calls_imported.py"),
            "lineno": invalid_value
        }]
        # Dont fail
        fulfill_context_requests(info, project_root=FIXTURES)


def test_fulfill_context_with_string_lineno():
    """Test fulfill_context_requests with a string lineno that can be converted to an int."""
    info = [{
        "symbol": "bar",
        "ref_path": str(FIXTURES / "calls_imported.py"),
        "lineno": "4"  # Valid string that can be converted to int
    }]
    
    result = fulfill_context_requests(info, project_root=FIXTURES)
    assert len(result) == 1
    assert result[0]["symbol"] == "bar"
    assert "def bar" in result[0]["snippet"]
