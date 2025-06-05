import pytest
from pathlib import Path

from cybermule.commands.suggest_test import parse_pytest_path
from cybermule.symbol_resolution import extract_test_definitions


def test_parse_pytest_path_with_function():
    """Test parsing pytest path with function specification."""
    file_path, test_identifier = parse_pytest_path("tests/test_example.py::test_function")
    
    assert file_path == Path("tests/test_example.py")
    assert test_identifier == "test_function"


def test_parse_pytest_path_with_class_method():
    """Test parsing pytest path with class and method specification."""
    file_path, test_identifier = parse_pytest_path("tests/test_example.py::TestClass::test_method")
    
    assert file_path == Path("tests/test_example.py")
    assert test_identifier == "TestClass::test_method"


def test_parse_pytest_path_file_only():
    """Test parsing pytest path with only file specification."""
    file_path, test_identifier = parse_pytest_path("tests/test_example.py")
    
    assert file_path == Path("tests/test_example.py")
    assert test_identifier is None


def test_parse_pytest_path_nested_path():
    """Test parsing pytest path with nested directory structure."""
    file_path, test_identifier = parse_pytest_path("deep/nested/path/test_file.py::test_func")
    
    assert file_path == Path("deep/nested/path/test_file.py")
    assert test_identifier == "test_func"


@pytest.fixture
def test_file_content():
    """Test file content fixture."""
    return '''
import unittest

def test_simple_function():
    """A simple test function."""
    assert True

def test_another_function():
    """Another test function."""
    result = 1 + 1
    assert result == 2

def not_a_test():
    """This is not a test function."""
    pass

class TestClass:
    def test_method(self):
        """A test method in a class."""
        assert True
        
    def not_a_test_method(self):
        """Not a test method."""
        
        def test_this_is_also_not_a_test():
          pass

def test_complex_function():
    """A more complex test function."""
    data = [1, 2, 3]
    for item in data:
        assert item > 0
'''


def test_extract_all_test_functions(tmp_path, test_file_content):
    """Test extracting all test functions from a file."""
    test_file = tmp_path / "test_example.py"
    test_file.write_text(test_file_content)
    
    results = extract_test_definitions(test_file)
    
    assert len(results) == 4
    assert results[0]['symbol'] == 'test_simple_function'
    assert results[1]['symbol'] == 'test_another_function'
    assert results[2]['symbol'] == 'test_method'
    assert results[3]['symbol'] == 'test_complex_function'


def test_extract_specific_test_function_with_class(tmp_path, test_file_content):
    """Test extracting a specific test function by name."""
    test_file = tmp_path / "test_example.py"
    test_file.write_text(test_file_content)
    
    results = extract_test_definitions(test_file, 'TestClass::test_method')
    
    assert len(results) == 1
    assert results[0]['symbol'] == 'test_method'


def test_extract_specific_test_function(tmp_path, test_file_content):
    """Test extracting a specific test function by name."""
    test_file = tmp_path / "test_example.py"
    test_file.write_text(test_file_content)
    
    results = extract_test_definitions(test_file, 'test_simple_function')
    
    assert len(results) == 1
    assert results[0]['symbol'] == 'test_simple_function'


def test_extract_nonexistent_function(tmp_path, test_file_content):
    """Test extracting a function that doesn't exist."""
    test_file = tmp_path / "test_example.py"
    test_file.write_text(test_file_content)
    
    results = extract_test_definitions(test_file, 'nonexistent_test')
    
    assert len(results) == 0


def test_extract_from_file_with_no_tests(tmp_path):
    """Test extracting from a file with no test functions."""
    content_no_tests = '''
def regular_function():
    return "not a test"

class RegularClass:
    def method(self):
        pass
'''
    test_file = tmp_path / "no_tests.py"
    test_file.write_text(content_no_tests)
    
    results = extract_test_definitions(test_file)
    assert len(results) == 0


def test_extract_handles_file_read_error():
    """Test that extract_test_definitions handles file read errors gracefully."""
    nonexistent_path = Path("/nonexistent/path/test.py")
    
    results = extract_test_definitions(nonexistent_path)
    
    assert len(results) == 0
