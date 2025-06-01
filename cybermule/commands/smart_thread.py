# cybermule/commands/smart_thread.py

import typer
from cybermule.memory.memory_graph import MemoryGraph
from cybermule.executors import run_codegen, run_refactor, fix_errors, suggest_tests
from cybermule.utils.task_planner import parse_natural_task_string, plan_generate_or_refactor


def run(ctx: typer.Context, task: str = typer.Argument(None)):
    config = ctx.obj.get("config", {})
    graph = MemoryGraph()

    try:
        plan = parse_natural_task_string(task) if task else plan_generate_or_refactor()
    except Exception as e:
        typer.echo(f"❌ Failed to parse task string: {e}")
        raise typer.Exit(code=1)

    source_file = str(plan["file"])

    if plan["mode"] == "generate":
        codegen_id = run_codegen.execute(
            graph,
            task_description=plan["goal"],
        )
    else:
        codegen_id = run_refactor.execute(
            graph=graph,
            file=plan["file"],
            goal=plan["goal"],
            context=plan["context"],
            preview=False,
            config=config
        )

    test_id = run_tests.execute(graph)
    if graph.get(test_id)["status"] == "TESTS_FAILED":
        fix_errors.execute(graph, config=config, parent_node_id=codegen_id, test_id=test_id)
        test_id = run_tests.execute(graph)

    suggest_tests.execute(graph, source_file=source_file)

    typer.echo("\n🎯 Smart thread complete. Use `history` or `describe-node` to explore the memory graph.")
