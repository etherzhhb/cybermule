from cybermule.tools.memory_graph import MemoryGraph
from cybermule.providers.llm_provider import LLMProvider
from cybermule.tools.config_loader import get_prompt_path
from langchain.prompts import PromptTemplate
from pathlib import Path

def execute(graph: MemoryGraph, task_description: str, debug_prompt: bool = False) -> str:
    node_id = graph.new(f"Generate code: {task_description}")

    prompt_path = Path(__file__).parent.parent / get_prompt_path("generate_code.j2")
    template = PromptTemplate.from_template(prompt_path.read_text())
    prompt = template.format(task_description=task_description)

    if debug_prompt:
        print("\n--- Generate Code Prompt ---\n" + prompt + "\n--- End Prompt ---\n")

    llm = LLMProvider()
    code = llm.generate(prompt)

    graph.update(node_id, prompt=prompt, response=code, status="GENERATED")
    return node_id