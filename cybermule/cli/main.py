import importlib
from pathlib import Path
import typer
import logging
import yaml

from cybermule.commands import generate, review_commit, history, show_log, filter, refactor

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
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
    debug_prompt: bool = typer.Option(False, help="Print the rendered prompt before sending to LLM")
):
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(level=level)
    logging.debug("Verbose mode enabled")

    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    ctx.obj = {"config": config, "debug_prompt": debug_prompt}

app.command("generate")(generate.run)
app.command("review-commit")(review_commit.run)
app.command("history")(history.run)
app.command("show-log")(show_log.run)
app.command("filter")(filter.run)
app.command("refactor")(refactor.run)

# Lazily import check-llm command
def lazy_command(module: str, attr: str = "run"):
    def _load():
        mod = importlib.import_module(module)
        return getattr(mod, attr)
    return _load()

app.command("check-llm")(lazy_command("cybermule.commands.check_llm"))


if __name__ == "__main__":
    app()
