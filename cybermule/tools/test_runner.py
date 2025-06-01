import subprocess
import re
import os
from pathlib import Path


def prepare_test_environment(venv_path: Path = Path("venv"), project_root: Path = Path(".")) -> Path:
    """
    Prepare the test environment using a virtualenv Python executable.

    Args:
        venv_path: Path to the virtual environment directory.
        project_root: Path to the root of the project to install in editable mode.

    Returns:
        Path to the venv's Python executable, which should be used for all test subprocesses.
    """
    python_exe = venv_path / "bin" / "python"
    if os.name == "nt":
        python_exe = venv_path / "Scripts" / "python.exe"

    if not python_exe.exists():
        raise RuntimeError(f"Virtualenv Python not found at: {python_exe}")

    try:
        subprocess.run([str(python_exe), "-m", "pip", "install", "-e", str(project_root)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[prepare_test_environment] pip install failed: {e}")
        raise

    return python_exe


def run_pytest(maxfail: int = 10, tb_mode: str = "short", python_exe: Path | None = None) -> tuple[int, list[str]]:
    """
    Run the full test suite using pytest and return the number of failed tests and their tracebacks.

    Args:
        maxfail: Maximum number of failures to allow before pytest exits early.
        tb_mode: Traceback verbosity mode ('auto', 'long', 'short', 'no').
        python_exe: Optional Python executable (e.g., from venv). Defaults to "pytest" in PATH.

    Returns:
        failure_count: Number of failed tests.
        tracebacks: List of raw traceback strings from failed tests.
    """
    # TODO: Consider refactoring shared subprocess logic with run_single_test
    try:
        cmd = [str(python_exe), "-m", "pytest"] if python_exe else ["pytest"]
        cmd += [f"--maxfail={maxfail}", f"--tb={tb_mode}", "-q"]

        result = subprocess.run(
            cmd,
            check=False,
            text=True,
            capture_output=True
        )
        output = result.stdout + "\n" + result.stderr
        failures = re.findall(r"=+ FAILURES =+\n(.*?)\n=+", output, re.DOTALL)
        return len(failures), failures
    except Exception as e:
        print(f"[run_pytest] Exception: {e}")
        return -1, []


def run_single_test(test_name: str, tb_mode: str = "short", python_exe: Path | None = None) -> tuple[bool, str]:
    """
    Run a single test using pytest and return whether it passed and its traceback if failed.

    Args:
        test_name: Name of the test function or file::function identifier.
        tb_mode: Traceback verbosity mode ('auto', 'long', 'short', 'no').
        python_exe: Optional Python executable (e.g., from venv). Defaults to "pytest" in PATH.

    Returns:
        success: True if test passed, False otherwise.
        traceback: Error traceback string if failed, else empty string.
    """
    # TODO: Consider refactoring shared subprocess logic with run_pytest
    try:
        cmd = [str(python_exe), "-m", "pytest"] if python_exe else ["pytest"]
        cmd += ["-q", "-k", test_name, f"--tb={tb_mode}"]

        result = subprocess.run(
            cmd,
            check=False,
            text=True,
            capture_output=True
        )
        output = result.stdout + "\n" + result.stderr
        failed = result.returncode != 0
        if failed:
            traceback_match = re.search(r"=+ FAILURES =+\n(.*?)\n=+", output, re.DOTALL)
            traceback = traceback_match.group(1).strip() if traceback_match else output
        else:
            traceback = ""
        return not failed, traceback
    except Exception as e:
        print(f"[run_single_test] Exception: {e}")
        return False, str(e)


def get_first_failure(tracebacks: list[str]) -> tuple[str, str]:
    """
    Return the name and traceback of the first failed test.

    Args:
        tracebacks: List of traceback strings from run_pytest.

    Returns:
        test_name: The test name string (approximation).
        traceback: The corresponding traceback.
    """
    if not tracebacks:
        return "", ""

    traceback = tracebacks[0]
    match = re.search(r"_______+ ([\w\.\-/:]+) ", traceback)
    test_name = match.group(1) if match else "unknown"
    return test_name, traceback
