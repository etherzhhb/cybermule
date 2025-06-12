from pathlib import Path
from typing import Optional
import typer
from typer import Context

from cybermule.executors.git_review import review_commit_with_llm
from cybermule.memory.memory_graph import MemoryGraph
from cybermule.tools.test_runner import run_test, get_first_failure, run_single_test
from cybermule.executors.analyzer import summarize_traceback, analyze_failure_with_llm
from cybermule.executors.apply_code_change import apply_code_change, describe_change_plan


def run(
    ctx: Context,
    summarize_only: bool = typer.Option(False, help="Only summarize the failure without applying a fix."),
    test: Optional[str] = typer.Option(None, help="Run only the specified test (e.g. path/to/test.py::func)"),
    log: Optional[Path] = typer.Option(None, exists=True, help="Read the log file for stack trace instead of running pytest"),
    review_commit: bool = typer.Option(False, help="Run a commit review before analyzing test failure."),
    dry_run: bool = typer.Option(
      False,
      "--dry-run",
      help="Only show new tests without applying them",
    ),
):
    config = ctx.obj.get("config", {})
    graph = MemoryGraph()

    review_node_id = None
    if review_commit:
        typer.echo("[run_and_fix] Reviewing latest commit...")
        review, review_node_id = review_commit_with_llm(config, graph=graph)
        typer.echo(review)

    if log is not None:
        typer.echo(f"[run_and_fix] ❌ reading stack trace from log: {log}\n")
        traceback = log.read_text()
    else:
        test_name, traceback = run_and_get_first_failure(test, config)
        typer.echo(f"[run_and_fix] ❌ First failed test: {test_name}\n")
    
    if summarize_only:
        typer.echo("[run_and_fix] 🔍 LLM summary of the failure:")
        summary, _ = summarize_traceback(traceback, config, graph=graph,
                                        parent_id=review_node_id)
        typer.echo(summary)
        return

    typer.echo("[run_and_fix] 🛠 LLM proposed fix:")
    fix_plan, analyze_id = analyze_failure_with_llm(traceback, config, graph=graph,
                                                    parent_id=review_node_id)

    fix_description = fix_plan.get('fix_description', '')
    # Get file paths and message from helper function
    file_paths, message = describe_change_plan(fix_plan, config)


    typer.echo(f"🧾 Fix description: {fix_description}")

    if  dry_run:
        typer.echo("🎯 Dry run, not applying change")
        return

    apply_code_change(description=fix_description,
                      file_paths=file_paths, message=message,
                      config=config, graph=graph, parent_id=analyze_id,
                      operation_type="fix")


def run_and_get_first_failure(test, config):
  typer.echo("[run_and_fix] Running pytest...")
  if test:
    typer.echo(f"[run_and_fix] Running single test: {test}")
    passed, traceback = run_single_test(test_name=test, config=config)
    if passed:
      typer.echo("[run_and_fix] ✅ Test passed. Nothing to fix.")
      raise typer.Exit(code=0)
    return test, traceback

  typer.echo("[run_and_fix] Running full test suite...")
  failure_count, tracebacks = run_test(config)
  if failure_count == 0:
    typer.echo("[run_and_fix] ✅ All tests passed. Nothing to fix.")
    raise typer.Exit(code=0)

  return get_first_failure(tracebacks)
