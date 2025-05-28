from tools.memory_graph import MemoryGraph
from providers.llm_provider import ClaudeBedrockProvider
from tools.config_loader import get_prompt_path
from langchain.prompts import PromptTemplate
from pathlib import Path

def execute(graph: MemoryGraph, parent_node_id: str, debug_prompt: bool = False) -> str:
    node_id = graph.new("Fix code based on test errors", parent=parent_node_id)

    # Get previous code and test error
    prev_code = graph.data[parent_node_id].get("response", "")
    test_error = ""
    for nid, node in graph.data.items():
        if node.get("task", "").startswith("Run unit tests") and node.get("parent") == parent_node_id:
            test_error = node.get("response", "")
            break

    prompt_path = Path(__file__).parent.parent / get_prompt_path("fix_code_error.j2")
    template = PromptTemplate.from_template(prompt_path.read_text())
    prompt = template.format(previous_code=prev_code, test_errors=test_error)

    if debug_prompt:
        print("\n--- Fix Code Prompt ---\n" + prompt + "\n--- End Prompt ---\n")

    llm = ClaudeBedrockProvider()
    fixed_code = llm.generate(prompt)

    graph.update(node_id, prompt=prompt, response=fixed_code, status="RETRIED")
    return node_id