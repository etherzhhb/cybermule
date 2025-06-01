import typer
from pathlib import Path
from cybermule.memory.memory_graph import MemoryGraph
from cybermule.providers.llm_provider import get_llm_provider
from cybermule.utils.config_loader import get_prompt_path
from langchain.prompts import PromptTemplate
import json

def run(task: str = typer.Argument(..., help="Task description")):

    graph = MemoryGraph()
    node_id = graph.new(f"Plan: {task}")

    prompt_path = get_prompt_path("plan_task.j2")
    template = PromptTemplate.from_template(prompt_path.read_text())
    prompt = template.format(task_description=task)

    llm = get_llm_provider()
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