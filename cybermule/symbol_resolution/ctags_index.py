import json
import subprocess
from pathlib import Path
from typing import Dict, Optional

_symbol_index_cache: Dict[str, Dict[str, Dict]] = {}


def _generate_symbol_index(project_root: Path) -> Dict[str, Dict[str, str]]:
    """
    Uses ctags to generate a symbol index for Python files in the given directory.
    Returns a dict: symbol -> {file, line, kind}
    """
    if str(project_root) in _symbol_index_cache:
        return _symbol_index_cache[str(project_root)]

    cmd = [
        "ctags",
        "-R",
        "--fields=+n",  # include line numbers
        "--languages=Python",
        "--output-format=json",
        str(project_root)
    ]
    try:
        output = subprocess.check_output(cmd, universal_newlines=True)
    except subprocess.CalledProcessError as e:#
        print(f"[ctags] Failed: {e}")
        return {}

    index: Dict[str, Dict[str, str]] = {}

    for line in output.strip().splitlines():
        try:
            tag = json.loads(line)
            name = tag.get("name")
            path = tag.get("path")
            line = str(tag.get("line", ""))
            kind = tag.get("kind")

            if name and path:
                index[name] = {
                    "file": path,
                    "line": line,
                    "kind": kind
                }
        except Exception as e:
            print(f"[WARN] Failed to parse ctags JSON line: {e}")

    return index


def _lookup_symbol(symbol: str, project_root: Path) -> Optional[Dict[str, str]]:
    index = _generate_symbol_index(project_root)
    return index.get(symbol)