from typing import Optional
import typer
from typer import Context

from cybermule.executors.git_review import review_commit_with_llm
from cybermule.memory.memory_graph import MemoryGraph
from cybermule.tools.test_runner import run_test, get_first_failure, run_single_test
from cybermule.executors.analyzer import summarize_traceback, analyze_failure_with_llm
from cybermule.utils.patch_utils import apply_fix

def run(
    ctx: Context,
    summarize_only: bool = typer.Option(False, help="Only summarize the failure without applying a fix."),
    test: Optional[str] = typer.Option(None, help="Run only the specified test (e.g. path/to/test.py::func)"),
    review_commit: bool = typer.Option(False, help="Run a commit review before analyzing test failure.")
):
    config = ctx.obj.get("config", {})
    graph = MemoryGraph()

    review_node_id = None
    if review_commit:
        typer.echo("[run_and_fix] Reviewing latest commit...")
        review, review_node_id = review_commit_with_llm(config, graph=graph)
        typer.echo(review)

    typer.echo("[run_and_fix] Running pytest...")

    if test:
        typer.echo(f"[run_and_fix] Running single test: {test}")
        passed, traceback = run_single_test(test_name=test, config=config)
        if passed:
            typer.echo("[run_and_fix] ✅ Test passed. Nothing to fix.")
            raise typer.Exit(code=0)
        test_name = test
        failure_count = 1
    else:
        typer.echo("[run_and_fix] Running full test suite...")
        failure_count, tracebacks = run_test(config)
        if failure_count == 0:
            typer.echo("[run_and_fix] ✅ All tests passed. Nothing to fix.")
            raise typer.Exit(code=0)
        test_name, traceback = get_first_failure(tracebacks)

    typer.echo(f"[run_and_fix] ❌ First failed test: {test_name}\n")
    
    if summarize_only:
        typer.echo("[run_and_fix] 🔍 LLM summary of the failure:")
        summary, _ = summarize_traceback(traceback, config, graph=graph,
                                        parent_id=review_node_id)
        typer.echo(summary)
        return

    typer.echo("[run_and_fix] 🛠 LLM proposed fix:")
    fix_plan, _ = analyze_failure_with_llm(traceback, config, graph=graph,
                                           parent_id=review_node_id)

    typer.echo(f"🧾 Fix description: {fix_plan.get('fix_description', '')}")
    apply_fix(fix_plan, graph=graph)
