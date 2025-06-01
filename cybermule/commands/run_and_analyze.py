import typer
from typer import Context

from cybermule.tools.test_runner import run_pytest, get_first_failure
from cybermule.executors.analyzer import summarize_traceback, analyze_failure_with_llm

def run(
    ctx: Context,
    summarize: bool = typer.Option(True, help="Use LLM to summarize the failure instead of returning a fix plan."),
    maxfail: int = typer.Option(5, help="Stop after N failures.")
):
    config = ctx.obj.get("config", {})
    typer.echo("[run_and_analyze] Running pytest...")

    failure_count, tracebacks = run_pytest(maxfail=maxfail)

    if failure_count == 0:
        typer.echo("[run_and_analyze] ✅ All tests passed. Nothing to analyze.")
        raise typer.Exit(code=0)

    test_name, traceback = get_first_failure(tracebacks)
    typer.echo(f"[run_and_analyze] ❌ First failed test: {test_name}\n")

    if summarize:
        typer.echo("[run_and_analyze] 🔍 LLM summary of the failure:")
        summary = summarize_traceback(traceback, config)
        typer.echo(summary)
    else:
        typer.echo("[run_and_analyze] 🛠 LLM proposed fix:")
        fix = analyze_failure_with_llm(traceback, config)
        typer.echo(fix)
