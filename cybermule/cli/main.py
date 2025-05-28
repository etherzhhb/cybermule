import typer
from commands import generate, review_commit, history, show_log, filter

app = typer.Typer()

app.command("generate")(generate.run)
app.command("review-commit")(review_commit.run)
app.command("history")(history.run)
app.command("show-log")(show_log.run)
app.command("filter")(filter.run)

if __name__ == "__main__":
    app()

app.command("check-llm")(importlib.import_module("cybermule.commands.check_llm").run)
