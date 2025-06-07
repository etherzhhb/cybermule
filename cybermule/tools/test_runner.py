import re
import subprocess
from pathlib import Path
import typer


def run_shell_block(label: str, script_path: str | None = None,
                    command_block: str | None = None, may_fail=False) -> str:
    """
    Execute a shell script or inline shell command block and return combined output.

    Args:
        label: Descriptive label for logging (e.g., "Setup", "Test").
        script_path: Path to a bash script (if used).
        command_block: Shell command block as string (if used).

    Returns:
        Captured output (stdout + stderr) as a string.

    Raises:
        RuntimeError if the script or command fails.
    """
    if script_path:
        typer.echo(f"[{label}] Running script: {script_path}")
        result = subprocess.run(["bash", script_path], text=True, capture_output=True)
    elif command_block:
        typer.echo(f"[{label}] Running inline shell block...\n{command_block}\n")
        result = subprocess.run(command_block, shell=True, executable="/bin/bash", text=True, capture_output=True)
    else:
        raise ValueError(f"[{label}] No script or command provided")

    output = result.stdout + "\n" + result.stderr

    if may_fail or result.returncode == 0:
        return output

    raise RuntimeError(f"[{label}] Failed with exit code {result.returncode}:\n{output.strip()}")


def prepare_test_environment(config: dict) -> None:
    """
    Prepare the test environment using the 'setup_command' from config.

    Args:
        config: Dict containing setup_command or setup_script.
    """
    run_shell_block(
        label="Setup",
        script_path=config.get("setup_script"),
        command_block=config.get("setup_command"),
    )

def run_test(config: dict) -> tuple[int, list[str]]:
    """
    Run the full test suite using config and return number of failures and tracebacks.

    Args:
        config: Dict containing test_command or test_script.

    Returns:
        Tuple of (failure_count, list of traceback blocks).
    """
    try:
        prepare_test_environment(config)

        output = run_shell_block(
            label="Test",
            script_path=config.get("test_script"),
            command_block=config.get("test_command"),
            may_fail=True,
        )

        return extract_failures_blocks(output)

    except Exception as e:
        typer.echo(f"[run_test] Exception: {e}")
        return -1, []


def extract_failures_blocks(output):
  # Find the full FAILURES section - accommodate variable number of equal signs
  # and match until "short test summary info" or end of string
  failures_section_match = re.search(r"={3,} FAILURES ={3,}\n(.*?)(?:={3,} short test summary info ={3,}|$)", output,
                                     re.DOTALL)
  if not failures_section_match:
    return 0, []

  failures_section = failures_section_match.group(1)
  # Now extract each failure block that starts with test name surrounded by underscores
  pattern = r"_{6,} ([^\n]+) _{6,}\n(.*?)(?=(?:_{6,} |$))"
  matches = re.findall(pattern, failures_section, re.DOTALL)
  failure_blocks = [f"{name}\n{trace.strip()}" for name, trace in matches]
  return len(failure_blocks), failure_blocks


def run_single_test(test_name: str, config: dict) -> tuple[bool, str]:
    """
    Run a single test using config-specified command/script. Return (success, traceback).

    Args:
        test_name: Name of the test (e.g. test_file.py::test_func).
        config: Dict with keys:
            - single_test_command: shell string with {test_name}
            - single_test_script: path to bash script

    Returns:
        Tuple of (passed: bool, traceback: str)
    """
    try:
        prepare_test_environment(config)

        if "single_test_command" in config:
            command = config["single_test_command"].format(test_name=test_name)
            output = run_shell_block("SingleTest",
                                     command_block=command,
                                     may_fail=True)
        elif "single_test_script" in config:
            output = run_shell_block("SingleTest",
                                     script_path=config["single_test_script"],
                                     may_fail=True)
        else:
            raise ValueError("No single test runner configured in config")

        match = re.search(r"={3,} FAILURES ={3,}\n(.*?)(?:={3,} short test summary info ={3,}|$)", output, re.DOTALL)
        if match:
            return False, match.group(1).strip()
        return True, ""
    except Exception as e:
        return False, str(e)


def get_first_failure(tracebacks: list[str]) -> tuple[str, str]:
    """
    Return the name and traceback of the first failed test.

    Args:
        tracebacks: List of raw traceback blocks.

    Returns:
        Tuple of (test_name, traceback).
    """
    if not tracebacks:
        return "", ""

    traceback = tracebacks[0]
    match = re.search(r"_{6,} ([\w\.\-/:]+) ", traceback)
    test_name = match.group(1) if match else "unknown"
    return test_name, traceback
