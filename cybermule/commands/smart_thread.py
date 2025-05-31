# cybermule/commands/smart_thread.py

import typer
from cybermule.memory.memory_graph import MemoryGraph
from cybermule.executors import run_codegen, run_refactor, run_tests, fix_errors, suggest_tests
from cybermule.utils.task_planner import plan_generate_or_refactor


def run(ctx: typer.Context):
    config = ctx.obj.get("config", {})
    debug = ctx.obj.get("debug_prompt", False)
    graph = MemoryGraph()

    plan = plan_generate_or_refactor()
    source_file = str(plan["file"])

    if plan["mode"] == "generate":
        codegen_id = run_codegen.execute(
            graph,
            task_description=plan["goal"],
            debug_prompt=debug
        )
    else:
        codegen_id = run_refactor.execute(
            graph=graph,
            file=plan["file"],
            goal=plan["goal"],
            context=plan["context"],
            preview=False,
            debug_prompt=debug,
            config=config
        )

    test_id = run_tests.execute(graph, debug=debug)
    if graph.data[test_id]["status"] == "TESTS_FAILED":
        fix_errors.execute(graph, parent_node_id=codegen_id, debug_prompt=debug)
        test_id = run_tests.execute(graph, debug=debug)

    suggest_tests.execute(graph, source_file=source_file, debug_prompt=debug)

    typer.echo("\n🎯 Smart thread complete. Use `history` or `describe-node` to explore the memory graph.")
