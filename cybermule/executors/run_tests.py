import subprocess
import typer
from cybermule.memory.memory_graph import MemoryGraph

def execute(graph: MemoryGraph, debug: bool = False) -> str:
    node_id = graph.new("Run unit tests")

    try:
        result = subprocess.run(["pytest", "-v"], capture_output=True, text=True)
        output = result.stdout + "\n" + result.stderr
        status = "TESTS_PASSED" if result.returncode == 0 else "TESTS_FAILED"
    except Exception as e:
        output = str(e)
        status = "ERROR"

    if debug:
        typer.echo("\n--- Test Output ---")
        typer.echo(output)
        typer.echo("--- End Test Output ---\n")

    graph.update(node_id, prompt="Run unit tests", response=output, status=status)
    return node_id
