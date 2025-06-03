import ast
from pathlib import Path
from typing import Optional, Dict

from .ctags_index import lookup_symbol, generate_symbol_index
from .ast_lookup import extract_symbol_definition, extract_function_at_line


def resolve_symbol(symbol: str, project_root: Path) -> Optional[Dict[str, str]]:
    """
    Resolves a symbol to its code definition.
    Falls back from ctags → AST.
    Returns dict with keys: file, symbol, start_line, snippet, etc.
    """

    result = lookup_symbol(symbol, project_root)
    if result:
        file_path = Path(project_root) / result["file"]
        definition = extract_symbol_definition(file_path, symbol)
        if definition:
            return definition

    return None

def extract_definition_by_callsite(path: Path, line_number: int, project_root: Optional[Path] = None) -> Optional[Dict[str, str]]:
    """
    Find function call on given line, extract callee name, and resolve symbol using centralized logic.
    """
    project_root = project_root or Path(".").resolve()

    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        candidates = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node, "lineno", -1) == line_number:
                func_node = node.func
                if isinstance(func_node, ast.Name):
                    candidates.append(func_node.id)
                elif isinstance(func_node, ast.Attribute):
                    candidates.append(func_node.attr)

        if not candidates:
            return None

        for symbol in candidates:
            result = resolve_symbol(symbol, project_root=project_root)
            if result:
                return result

    except Exception as e:
        print(f"[extract_definition_by_callsite] Failed for {path}:{line_number}: {e}")
    return None

__all__ = [
    "resolve_symbol",
    "lookup_symbol",
    "generate_symbol_index",
    "extract_symbol_definition",
    "extract_function_at_line",
    "extract_definition_by_callsite",  # ← ADD THIS
]
