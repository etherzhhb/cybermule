import importlib
import os
from pathlib import Path
import typer
import logging
import yaml

from cybermule.commands import (
    review_commit,
    history,
    filter,
    refactor,
    run_and_fix,
    smart_thread,
)

app = typer.Typer()


@app.callback()
def main(
    ctx: typer.Context,
    config_file: Path = typer.Option(
        "config.yaml",
        "--config",
        "-c",
        help="Path to YAML config file",
        exists=True,
        file_okay=True,
        readable=True,
    ),
    cwd: Path = typer.Option(
        None,
        "--cwd",
        help="Change to this directory before executing commands",
        exists=True,
        dir_okay=True,
        readable=True,
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
):
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(level=level)
    logging.debug("Verbose mode enabled")

    # Change working directory if specified
    if cwd:
        try:
            original_cwd = os.getcwd()
            os.chdir(cwd)
            logging.debug(f"Changed working directory from {original_cwd} to {cwd}")
        except OSError as e:
            typer.echo(f"Error: Could not change to directory '{cwd}': {e}", err=True)
            raise typer.Exit(1)

    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    ctx.obj = {"config": config}


app.command("review-commit")(review_commit.run)
app.command("history")(history.run)
app.command("filter")(filter.run)
app.command("refactor")(refactor.run)
app.command("smart_thread")(smart_thread.run)
app.command("run-and-fix")(run_and_fix.run)


# Lazily import check-llm command
def lazy_command(module: str, attr: str = "run"):
    def _load():
        mod = importlib.import_module(module)
        return getattr(mod, attr)

    return _load()


app.command("check-llm")(lazy_command("cybermule.commands.check_llm"))


if __name__ == "__main__":
    app()
