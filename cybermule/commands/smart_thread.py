import typer
from tools.memory_graph import MemoryGraph
from executors import run_codegen, run_tests, fix_errors, suggest_tests

def run(task: str = typer.Argument(..., help="Describe the software task"),
        source_file: str = typer.Option(..., help="Source file to check test coverage"),
        debug: bool = typer.Option(False, help="Print prompts and outputs during execution")):

    graph = MemoryGraph()

    # Step 1: Generate code
    codegen_id = run_codegen.execute(graph, task_description=task, debug_prompt=debug)

    # Step 2: Run tests
    test_id = run_tests.execute(graph, debug=debug)

    test_status = graph.data[test_id]["status"]
    if test_status == "TESTS_FAILED":
        # Step 3: Fix errors
        fix_id = fix_errors.execute(graph, parent_node_id=codegen_id, debug_prompt=debug)
        # Step 4: Re-run tests after fix
        test_id = run_tests.execute(graph, debug=debug)

    # Step 5: Suggest tests
    suggest_tests.execute(graph, source_file=source_file, debug_prompt=debug)

    typer.echo("\n🎯 Smart thread complete. Run `history` or `describe-node` to review the memory graph.")