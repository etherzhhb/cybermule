from pathlib import Path
from typing import Optional, Dict

import typer

from .ctags_index import _lookup_symbol
from .tree_sitter_lookup import (
    extract_symbol_definition,
    extract_function_at_line, 
    extract_called_symbols_on_line,
    extract_called_symbols_in_function,
    extract_test_definitions
)

def resolve_symbol_in_function(ref_path: Path, ref_function: str, symbol: str, project_root: Optional[Path] = None) -> Optional[Dict[str, str]]:
    """
    Given a file and function name, locate the symbol used inside that function and resolve it.
    Used when LLM provides `ref_function` instead of a precise line number.
    """
    project_root = project_root or Path(".").resolve()

    try:
        candidates = extract_called_symbols_in_function(ref_path, ref_function)
        if symbol in candidates:
            return resolve_symbol(symbol, project_root)
    except Exception as e:
        typer.echo(f"[resolve_symbol_in_function] Error for {symbol} in {ref_path}:{ref_function} – {e}")
    return None

def resolve_symbol(symbol: str, project_root: Path) -> Optional[Dict[str, str]]:
    """
    Resolves a symbol to its code definition.
    Falls back from ctags → Tree-sitter.
    Returns dict with keys: file, symbol, start_line, snippet, etc.
    """
    result = _lookup_symbol(symbol, project_root)
    if result:
        file_path = Path(project_root) / result["file"]
        definition = extract_symbol_definition(file_path, symbol)
        if definition:
            return definition
    return None


def extract_definition_by_callsite(
    path: Path,
    line: int,
    symbol: str,
    project_root: Optional[Path] = None
) -> Optional[Dict[str, str]]:
    """
    Find function call on the given line, extract callee name, and resolve symbol using centralized logic.
    If `symbol` is provided, prioritize matching it.
    """
    project_root = project_root or Path(".").resolve()
    try:
        symbols = extract_called_symbols_on_line(path, line)
        for sym in symbols:
            if symbol and sym != symbol:
                continue
            result = resolve_symbol(symbol=sym, project_root=project_root)
            if result:
                return result
    except Exception as e:
        typer.echo(f"[extract_definition_by_callsite] Failed for {path}:{line}: {e}")
    return None



__all__ = [
    "resolve_symbol",
    "resolve_symbol_in_function",
    "extract_definition_by_callsite",
    "extract_function_at_line",
    "extract_symbol_definition",
    "extract_test_definitions",
]
