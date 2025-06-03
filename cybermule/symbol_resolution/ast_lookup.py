import ast
from pathlib import Path
from typing import Optional, Dict


def get_qualified_name(node: ast.AST, parent_map: Dict[ast.AST, ast.AST]) -> str:
    parts = []
    current = node
    while current:
        if isinstance(current, (ast.FunctionDef, ast.ClassDef)):
            parts.append(current.name)
        current = parent_map.get(current)
    return ".".join(reversed(parts))


def build_parent_map(tree: ast.AST) -> Dict[ast.AST, ast.AST]:
    parent_map = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parent_map[child] = parent
    return parent_map


def extract_symbol_definition(path: Path, symbol: str) -> Optional[Dict[str, str]]:
    """
    Given a Python file and a symbol name, returns its function/class definition.
    """
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
        print(f"[ast_lookup] Failed to extract {symbol} from {path}: {e}")
    return None


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