import typer
from pathlib import Path
from cybermule.tools.memory_graph import MemoryGraph
from cybermule.providers.llm_provider import LLMProvider
from cybermule.tools.config_loader import get_prompt_path
from langchain.prompts import PromptTemplate
import json

def run(task: str = typer.Argument(..., help="Task description"),
        debug_prompt: bool = typer.Option(False, help="Print prompt before sending to LLM")):

    graph = MemoryGraph()
    node_id = graph.new(f"Plan: {task}")

    prompt_path = Path(__file__).parent.parent / get_prompt_path("plan_task.j2")
    template = PromptTemplate.from_template(prompt_path.read_text())
    prompt = template.format(task_description=task)

    if debug_prompt:
        print("\n--- Plan Prompt ---\n" + prompt + "\n--- End Prompt ---\n")

    llm = LLMProvider()
    output = llm.generate(prompt)

    graph.update(node_id, prompt=prompt, response=output, status="PLANNED")

    try:
        steps = json.loads(output)
        for step in steps:
            desc = step.get("action") or step.get("description") or str(step)
            graph.new(desc, parent=node_id)
    except Exception as e:
        print(f"[!] Could not parse steps as JSON: {e}")

    typer.echo(f"✅ Plan created with {len(steps)} steps (if parsed). See node: {node_id}")