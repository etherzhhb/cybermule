import re
import ast
import sys
from pathlib import Path
from typing import List, Dict, Optional


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


def resolve_imported_symbol_path(caller_path: Path, symbol: str) -> Optional[Path]:
    try:
        source = caller_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == symbol or alias.asname == symbol:
                        module_parts = node.module.split(".") if node.module else []
                        project_root = Path(__file__).parent.parent.parent.resolve()
                        target_path = project_root.joinpath(*module_parts).with_suffix(".py")
                        return target_path if target_path.exists() else None
    except Exception as e:
        print(f"[resolve_imported_symbol_path] Failed for {symbol} in {caller_path}: {e}")
    return None


def extract_definition_by_callsite(path: Path, line_number: int, target_symbol: Optional[str] = None) -> Optional[Dict[str, str]]:
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        parent_map = build_parent_map(tree)

        candidates = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and hasattr(node, "lineno") and node.lineno == line_number:
                func_node = node.func
                name = None
                if isinstance(func_node, ast.Name):
                    name = func_node.id
                elif isinstance(func_node, ast.Attribute):
                    name = func_node.attr
                if name:
                    candidates.append(name)

        if target_symbol:
            candidates = [c for c in candidates if c == target_symbol]

        if not candidates:
            return None

        # Check same-file definitions
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name in candidates:
                    lines = source.splitlines()
                    snippet = "\n".join(lines[node.lineno - 1: node.end_lineno])
                    qualified = get_qualified_name(node, parent_map)
                    return {
                        "file": str(path),
                        "symbol": qualified,
                        "start_line": node.lineno,
                        "traceback_line": line_number,
                        "snippet": snippet
                    }

        # Resolve import
        for candidate in candidates:
            callee_path = resolve_imported_symbol_path(path, candidate)
            if callee_path:
                return extract_symbol_definition(callee_path, candidate)

    except Exception as e:
        print(f"[extract_definition_by_callsite] Failed to process {path}:{line_number}: {e}")
    return None


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

def extract_symbol_definition(path: Path, symbol: str) -> Optional[Dict[str, str]]:
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        parent_map = build_parent_map(tree)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name == symbol:
                    lines = source.splitlines()
                    snippet = "\n".join(lines[node.lineno - 1: node.end_lineno])
                    qualified = get_qualified_name(node, parent_map)
                    return {
                        "file": str(path),
                        "symbol": qualified,
                        "start_line": node.lineno,
                        "traceback_line": node.lineno,
                        "snippet": snippet
                    }

    except Exception as e:
        print(f"[extract_symbol_definition] Failed: {e}")
    return None
