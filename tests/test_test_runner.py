# test_test_runner.py
import pytest
import tempfile
from pathlib import Path
from textwrap import dedent
from cybermule.tools import test_runner  # adjust import to your actual module path


def test_run_shell_block_command_success():
    output = test_runner.run_shell_block(label="Test", command_block="echo Hello && echo World 1>&2")
    assert "Hello" in output
    assert "World" in output


def test_run_shell_block_command_failure():
    with pytest.raises(RuntimeError) as excinfo:
        test_runner.run_shell_block(label="Failing", command_block="exit 1")
    assert "exit code 1" in str(excinfo.value)


def test_run_shell_block_script_success(tmp_path):
    script = tmp_path / "ok.sh"
    script.write_text("echo script ok")
    script.chmod(0o755)

    output = test_runner.run_shell_block(label="Script", script_path=str(script))
    assert "script ok" in output


def test_prepare_test_environment_runs_setup_command():
    config = {"setup_command": "echo Preparing environment"}
    # just check that it runs without raising
    test_runner.prepare_test_environment(config)


def test_run_test_with_fake_failure(tmp_path):
    # Simulate a pytest-like failure using echo
    config = {
        "setup_command": "echo 'setup ok'",
        "test_command": dedent("""\
            echo '============================= FAILURES ============================='
            echo '________ test_sample.py::test_fail __________'
            echo 'assert 1 == 2'
            echo '=========================== short test summary ==========================='
        """)
    }
    count, tracebacks = test_runner.run_test(config)
    assert count == 1
    assert "assert 1 == 2" in tracebacks[0]

def test_run_test_with_fake_failure_2_tests():
    count, tracebacks = test_runner.extract_failures_blocks(dedent("""
      ...................................................................FF... [ 82%]
      ...............                                                          [100%]
      =================================== FAILURES ===================================
      ___________________ test_fulfill_context_with_invalid_lineno ___________________
      tests/test_symbol_resolution.py:110: in test_fulfill_context_with_invalid_lineno
          with pytest.raises(ValueError):
               ^^^^^^^^^^^^^^^^^^^^^^^^^
      E   Failed: DID NOT RAISE <class 'ValueError'>
      ----------------------------- Captured stderr call -----------------------------
      ctags: Warning: Enabling Cargo subparser may enable TOML parser.
      ctags: Warning: The current implementation of the TOML parser is broken.
      _________________ test_fulfill_context_with_non_numeric_lineno _________________
      tests/test_symbol_resolution.py:126: in test_fulfill_context_with_non_numeric_lineno
          with pytest.raises((TypeError, ValueError)):
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      E   Failed: DID NOT RAISE any of (<class 'TypeError'>, <class 'ValueError'>)
      ----------------------------- Captured stderr call -----------------------------
      ctags: Warning: Enabling Cargo subparser may enable TOML parser.
      ctags: Warning: The current implementation of the TOML parser is broken.
      =============================== warnings summary ===============================
      tests/test_analyzer.py: 6 warnings
      tests/test_cli.py: 9 warnings
      tests/test_memory_graph.py: 21 warnings
      =========================== short test summary info ============================
      FAILED tests/test_symbol_resolution.py::test_fulfill_context_with_invalid_lineno
      FAILED tests/test_symbol_resolution.py::test_fulfill_context_with_non_numeric_lineno
    """))
    assert count == 2
    assert "Failed: DID NOT RAISE <class 'ValueError'>" in tracebacks[0]
    assert "Failed: DID NOT RAISE any of (<class 'TypeError'>, <class 'ValueError'>)" in tracebacks[1]

def test_run_test_with_no_failures():
    config = {
        "setup_command": "echo setting up",
        "test_command": "echo 'All tests passed!'"
    }
    count, tracebacks = test_runner.run_test(config)
    assert count == 0
    assert tracebacks == []


def test_run_single_test_pass():
    config = {
        "setup_command": "echo 'env ok'",
        "single_test_command": "echo '[PASS] test: {test_name}'"
    }
    passed, tb = test_runner.run_single_test("my_test_func", config)
    assert passed is True
    assert tb == ""


def test_run_single_test_fail():
    config = {
        "setup_command": "echo 'env ok'",
        "single_test_command": dedent("""\
            echo '============================= FAILURES ============================='
            echo '________ test_file.py::test_broken '
            echo 'assert False'
            echo '=========================== short test summary ==========================='
        """)
    }
    passed, tb = test_runner.run_single_test("test_file.py::test_broken", config)
    assert passed is False
    assert "assert False" in tb


def test_get_first_failure_extracts_name():
    tracebacks = ["________ test_math.py::test_addition \nassert 1 + 1 == 3"]
    name, tb = test_runner.get_first_failure(tracebacks)
    assert name == "test_math.py::test_addition"
    assert "assert 1 + 1 == 3" in tb


def test_get_first_failure_empty_list():
    name, tb = test_runner.get_first_failure([])
    assert name == ""
    assert tb == ""
