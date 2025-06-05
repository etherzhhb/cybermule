import subprocess
import shlex
from typing import List, Sequence


def apply_with_aider(
    file_paths: List[str],
    message: str,
    extra_args: Sequence[str] = ()
) -> bool:
    """
    Calls Aider using --message mode with optional extra CLI arguments.

    Args:
        file_paths: List of files to apply edits to
        message: The instruction to pass to Aider
        extra_args: Optional extra CLI flags (e.g., ["--model", "gpt-4", "--dry-run"])

    Returns:
        True if Aider exited successfully, False otherwise
    """
    if not file_paths:
        raise ValueError("[aider_engine] No file paths provided to Aider.")

    cmd = ["aider", "--message", message] + list(extra_args) + file_paths

    try:
        print(f"[aider_engine] 🛠 Running: {' '.join(shlex.quote(arg) for arg in cmd)}")
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"[aider_engine] ❌ Aider failed with return code {e.returncode}")
        return False
    except FileNotFoundError:
        print("[aider_engine] ❌ Aider CLI not found. Is it installed and in your PATH?")
        return False
