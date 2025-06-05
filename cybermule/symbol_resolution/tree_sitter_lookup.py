from pathlib import Path
from typing import Optional, Dict, List
from tree_sitter import Language, Parser

import tree_sitter_python as tspython
from tree_sitter import Language, Parser
import typer

PY_LANGUAGE = Language(tspython.language())

parser = Parser(PY_LANGUAGE)

def parse_source(source: str):
    return parser.parse(bytes(source, "utf8"))


def get_node_text(node, source_bytes) -> str:
    return source_bytes[node.start_byte:node.end_byte].decode("utf8")


def walk_tree(node):
    yield node
    for child in node.children:
        yield from walk_tree(child)


def _extract_symbol_definition(path: Path, symbol: str) -> Optional[Dict[str, str]]:
    try:
        source = path.read_text(encoding="utf-8")
        source_bytes = source.encode("utf8")
        tree = parse_source(source)
        root = tree.root_node

        for node in walk_tree(root):
            if node.type in {"function_definition", "class_definition"}:
                name_node = node.child_by_field_name("name")
                if name_node and get_node_text(name_node, source_bytes) == symbol:
                    start_line = node.start_point[0] + 1
                    end_line = node.end_point[0] + 1
                    snippet = "\n".join(source.splitlines()[start_line - 1:end_line])
                    return {
                        "file": str(path),
                        "symbol": symbol,
                        "start_line": start_line,
                        "traceback_line": start_line,
                        "snippet": snippet,
                    }
    except Exception as e:
        typer.echo(f"[tree_sitter] Failed to extract {symbol} from {path}: {e}")
    return None


def extract_function_at_line(source_path: Path, line_number: int) -> Optional[Dict[str, str]]:
    try:
        source = source_path.read_text(encoding="utf-8")
        source_bytes = source.encode("utf8")
        tree = parse_source(source)
        root = tree.root_node

        best_node = None
        for node in walk_tree(root):
            if node.type in {"function_definition", "class_definition"}:
                start = node.start_point[0] + 1
                end = node.end_point[0] + 1
                if start <= line_number <= end:
                    if best_node is None or start > best_node.start_point[0]:
                        best_node = node

        if best_node:
            start_line = best_node.start_point[0] + 1
            end_line = best_node.end_point[0] + 1
            snippet = "\n".join(source.splitlines()[start_line - 1:end_line])
            name_node = best_node.child_by_field_name("name")
            symbol = get_node_text(name_node, source_bytes) if name_node else "<unknown>"
            return {
                "file": str(source_path),
                "symbol": symbol,
                "start_line": start_line,
                "traceback_line": line_number,
                "snippet": snippet,
            }

    except Exception as e:
        typer.echo(f"[tree_sitter] Failed to parse {source_path}: {e}")
    return None


def extract_called_symbols_on_line(path: Path, lineno: int) -> List[str]:
    results = []
    try:
        source = path.read_text(encoding="utf-8")
        source_bytes = source.encode("utf8")
        tree = parse_source(source)
        root = tree.root_node

        for node in walk_tree(root):
            if node.type == "call":
                line = node.start_point[0] + 1
                if line == lineno:
                    func_node = node.child_by_field_name("function")
                    if func_node:
                        if func_node.type == "identifier":
                            results.append(get_node_text(func_node, source_bytes))
                        elif func_node.type == "attribute":
                            name_node = func_node.child_by_field_name("attribute")
                            if name_node:
                                results.append(get_node_text(name_node, source_bytes))

    except Exception as e:
        typer.echo(f"[tree_sitter] Failed to extract calls on line {lineno} in {path}: {e}")
    return results

def extract_function_by_name(path: Path, func_name: str):
    source = path.read_text(encoding="utf-8")
    source_bytes = source.encode("utf-8")
    tree = parse_source(source)
    root = tree.root_node

    for node in walk_tree(root):
        if node.type == "function_definition":
            name_node = node.child_by_field_name("name")
            if name_node and get_node_text(name_node, source_bytes) == func_name:
                return node, source, source_bytes
    return None, source, source_bytes


def extract_called_symbols_in_function(path: Path, func_name: str) -> List[str]:
    node, source, source_bytes = extract_function_by_name(path, func_name)
    results = []
    if not node:
        return results

    for child in walk_tree(node):
        if child.type == "call":
            func_node = child.child_by_field_name("function")
            if func_node:
                if func_node.type == "identifier":
                    results.append(get_node_text(func_node, source_bytes))
                elif func_node.type == "attribute":
                    name_node = func_node.child_by_field_name("attribute")
                    if name_node:
                        results.append(get_node_text(name_node, source_bytes))
    return results
