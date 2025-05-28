import importlib

import typer
from cybermule.commands import generate, review_commit, history, show_log, filter

app = typer.Typer()

app.command("generate")(generate.run)
app.command("review-commit")(review_commit.run)
app.command("history")(history.run)
app.command("show-log")(show_log.run)
app.command("filter")(filter.run)

# Lazily import check-llm command
def lazy_command(module: str, attr: str = "run"):
    def _load():
        mod = importlib.import_module(module)
        return getattr(mod, attr)
    return _load()

app.command("check-llm")(lazy_command("cybermule.commands.check_llm"))


if __name__ == "__main__":
    app()
