import typer
from pathlib import Path
from typing import List, Optional

from cybermule.executors import run_refactor

def run(
    ctx: typer.Context,
    file: Path = typer.Argument(..., exists=True, help="Path to the file to refactor"),
    goal: str = typer.Option(..., help="Refactoring goal, e.g., 'extract class', 'rename variable'"),
    preview: bool = typer.Option(False, help="Show diff instead of applying changes"),
    context: Optional[List[str]] = typer.Option(
        None,
        "--context", "-c",
        help="Paths, directories, or glob patterns for files to provide context. Accepts globs and folders.",
    ),
):
    config = ctx.obj.get("config", {})

    run_refactor.execute(
        graph=None,
        file=file,
        goal=goal,
        context=context,
        preview=preview,
        config=config
    )
