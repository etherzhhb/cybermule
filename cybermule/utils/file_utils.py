from glob import glob
from pathlib import Path
from typing import List
import typer

def read_file_content(file_path: Path, verbose: bool = True) -> str:
    """
    Read content from a file with optional error message printing.

    Args:
        file_path: Path to the file to read
        verbose: If True, print errors to stderr

    Returns:
        Content of the file as a string
    """
    try:
        return file_path.read_text()
    except Exception as e:
        if verbose:
            typer.echo(f"Error reading file {file_path}: {e}", err=True)
        return ""


def resolve_context_inputs(entries: List[str]) -> List[Path]:
    """Resolve a list of globs, files, or dirs into valid .py files."""
    files = set()
    for entry in entries:
        path = Path(entry)
        if path.is_dir():
            files.update(path.rglob("*.py"))
        else:
            matches = glob(entry, recursive=True)
            files.update(Path(m) for m in matches if Path(m).is_file())
    return sorted(files)
