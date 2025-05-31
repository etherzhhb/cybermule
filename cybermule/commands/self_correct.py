import typer
from cybermule.memory.memory_graph import MemoryGraph
from cybermule.providers.llm_provider import get_llm_provider
from cybermule.tools.config_loader import get_prompt_path
from langchain.prompts import PromptTemplate
from cybermule.executors import run_tests, fix_errors

def run(node_id: str = typer.Argument(..., help="Node ID of failed code/test"),
        file: str = typer.Option(..., help="Source file to run tests on"),
        max_retries: int = typer.Option(2, help="How many times to retry fixing"),
        debug_prompt: bool = typer.Option(False, help="Print prompt before sending to LLM")):

    graph = MemoryGraph()

    for attempt in range(max_retries):
        node = graph.data[node_id]
        code = node.get("response", "")
        output = node.get("test_output", "") or node.get("response", "")

        # Diagnose the failure
        prompt_path = get_prompt_path("diagnose_failure.j2")
        template = PromptTemplate.from_template(Path(prompt_path).read_text())
        prompt = template.format(code=code, test_output=output)

        if debug_prompt:
            print("\n--- Diagnose Prompt ---\n" + prompt + "\n--- End Prompt ---\n")

        llm = get_llm_provider()
        diagnosis = llm.generate(prompt)

        # Log diagnosis
        diagnosis_id = graph.new("Diagnosis", parent=node_id)
        graph.update(diagnosis_id, prompt=prompt, response=diagnosis, status="DIAGNOSED")

        # Fix attempt
        fix_id = fix_errors.execute(graph, parent_node_id=diagnosis_id, debug_prompt=debug_prompt)

        # Test the fix
        result = run_tests.execute(graph, source_file=file, parent_node_id=fix_id, debug_prompt=debug_prompt)

        if "PASS" in result.upper() or "OK" in result.upper():
            typer.echo("✅ Self-correction succeeded.")
            return

        node_id = fix_id  # retry using this failed fix

    typer.echo("❌ Self-correction failed after retries.")