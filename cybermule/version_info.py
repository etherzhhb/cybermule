# cybermule/version_info.py

import os
from pathlib import Path
from typing import Dict
from contextlib import chdir

def get_version_info() -> Dict[str, str]:
    try:
        from cybermule import _version
        return {
            "version": _version.__version__,
            "git_commit": _version.__git_commit__,
        }
    except ImportError:
        try:
            from cybermule.utils.git_utils import get_latest_commit_sha

            cybermule_path = Path(__file__).resolve().parent

            with chdir(cybermule_path):
                commit = get_latest_commit_sha()

        except Exception:
            commit = "unknown"

        return {
            "version": "dev",
            "git_commit": commit,
        }
