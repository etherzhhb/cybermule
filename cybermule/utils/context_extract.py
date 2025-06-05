import re
from pathlib import Path
from typing import List, Dict, Optional

import typer

from cybermule.symbol_resolution import extract_function_at_line

def extract_locations(traceback: str) -> List[Dict]: 
    locations = []

    # classic Python style
    classic = re.findall(r'File "(.+?)", line (\d+), in (.+)', traceback)
    for file, line, func in classic:
        locations.append({"file": file, "line": int(line), "function": func})

    # pytest style (allow leading whitespace)
    pytest_style = re.findall(r'^\s*([^\s:]+):(\d+): in (.+)$', traceback, flags=re.MULTILINE)
    for file, line, func in pytest_style:
        locations.append({"file": file, "line": int(line), "function": func})

    return locations

def get_context_snippets(locations: List[Dict], fallback_window: int = 5) -> List[Dict]:
    context_snippets = []

    for loc in locations:
        file_path = Path(loc["file"])
        if not file_path.exists():
            continue

        line_no = loc["line"]
        match = extract_function_at_line(file_path, line_no)

        if match is None:
            lines = file_path.read_text(encoding="utf-8").splitlines()
            start = max(0, line_no - fallback_window - 1)
            end = min(len(lines), line_no + fallback_window)
            snippet = "\n".join(lines[start:end])
            context_snippets.append({
                "file": str(file_path),
                "symbol": None,
                "start_line": start + 1,
                "traceback_line": line_no,
                "snippet": snippet
            })
        else:
            context_snippets.append(match)

    return context_snippets
