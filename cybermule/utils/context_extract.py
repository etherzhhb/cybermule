import re
import ast
from pathlib import Path
from typing import List, Dict, Optional


def extract_locations(traceback: str) -> List[Dict]:
    pattern = re.compile(r'File "(.+?)", line (\d+), in (.+)')
    matches = pattern.findall(traceback)
    return [
        {"file": file, "line": int(line), "function": func}
        for file, line, func in matches
    ]


def build_parent_map(tree: ast.AST) -> Dict[ast.AST, ast.AST]:
    parent_map = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parent_map[child] = parent
    return parent_map


def get_qualified_name(node: ast.AST, parent_map: Dict[ast.AST, ast.AST]) -> str:
    parts = []
    current = node
    while current:
        if isinstance(current, (ast.FunctionDef, ast.ClassDef)):
            parts.append(current.name)
        current = parent_map.get(current)
    return ".".join(reversed(parts))


def extract_function_at_line(source_path: Path, line_number: int) -> Optional[Dict[str, str]]:
    try:
        source = source_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        parent_map = build_parent_map(tree)

        candidates = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                    if node.lineno <= line_number <= node.end_lineno:
                        candidates.append((node.lineno, node))

        if candidates:
            _, best_node = max(candidates, key=lambda x: x[0])
            lines = source.splitlines()
            snippet = "\n".join(lines[best_node.lineno - 1:best_node.end_lineno])
            qualified = get_qualified_name(best_node, parent_map)
            return {
                "file": str(source_path),
                "symbol": qualified,
                "start_line": best_node.lineno,
                "traceback_line": line_number,
                "snippet": snippet
            }

    except Exception as e:
        print(f"[extract_function_at_line] Failed to parse {source_path}: {e}")
    return None


def get_context_snippets(
    locations: List[Dict], fallback_window: int = 5
) -> Dict[str, Dict]:
    context = {}

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
            context[str(file_path)] = {
                "file": str(file_path),
                "symbol": None,
                "start_line": start + 1,
                "traceback_line": line_no,
                "snippet": snippet
            }
        else:
            context[str(file_path)] = match

    return context

