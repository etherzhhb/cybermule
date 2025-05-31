from pathlib import Path
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
