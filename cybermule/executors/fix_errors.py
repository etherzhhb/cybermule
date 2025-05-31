from cybermule.memory.memory_graph import MemoryGraph
from cybermule.providers.llm_provider import get_llm_provider
from cybermule.tools.config_loader import get_prompt_path
from cybermule.utils.template_utils import render_template
from langchain.prompts import PromptTemplate
from pathlib import Path


def execute(graph: MemoryGraph, config, parent_node_id: str, test_id:str, 
            debug_prompt: bool = False) -> str:
    node_id = graph.new("Fix code based on test errors", parent_id=parent_node_id)

    # Get previous code and test error
    parent_node = graph.get(parent_node_id)
    test_error = graph.get(test_id).get("response", "")

    prompt_path = Path(__file__).parent.parent / get_prompt_path(config, name="fix_code_error.j2")

    prompt = render_template(prompt_path, {
        "PYTHON_CODE": parent_node["generated_code"],
        "CODE_DIFF": parent_node.get("diff", ""),
        "CONTEXT_CODE": parent_node.get("context_code", ""),
        "PYTEST_RESULT": test_error,
    })

    if debug_prompt:
        print("\n--- Fix Code Prompt ---\n" + prompt + "\n--- End Prompt ---\n")

    llm = get_llm_provider(config)

    fixed_code = llm.generate(prompt)
    graph.update(node_id, prompt=prompt, response=fixed_code, status="RETRIED")
    return node_id