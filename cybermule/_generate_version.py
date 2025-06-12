# cybermule/_generate_version.py

import subprocess
from pathlib import Path

def write_version_file():
    version = "0.1.0"  # Or parse dynamically from pyproject.toml
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    except Exception:
        commit = "unknown"

    version_file = Path(__file__).parent / "_version.py"
    version_file.write_text(
        f'__version__ = "{version}"\n__git_commit__ = "{commit}"\n'
    )
