from cybermule.memory.history_utils import extract_chat_history, format_chat_history_as_text
from cybermule.memory.memory_graph import MemoryGraph
from cybermule.providers.llm_provider import get_llm_provider
from cybermule.utils.config_loader import get_prompt_path
from cybermule.utils.parsing import extract_first_json_block
from cybermule.utils.template_utils import render_template
import json


def _build_variant_entry(node_id, graph, config):
    node = graph.get(node_id)
    history = extract_chat_history(node, graph)
    history_txt = format_chat_history_as_text(history)
    
    prompt_path = get_prompt_path(config, name=node["prompt_template"])

    rendered_prompt = render_template(prompt_path, node.get("variables", {}))
    full_prompt = f"{history_txt}\n\n{rendered_prompt}"
    return {
        "node_id": node_id,
        "full_prompt": full_prompt,
        "response": node["response"],
    }


def evaluate_prompt_variants(node_ids, graph: MemoryGraph, config: dict, goal: str,
                              prompt_template="evaluate_prompt_variants.j2"):
    """
    Evaluate multiple prompt variants (identified by node IDs).

    Args:
        node_ids (List[str]): List of MemoryGraph node IDs with different prompt variants.
        graph (MemoryGraph): The memory graph.
        config (dict): LLM configuration.
        goal (str): Evaluation goal (e.g., clarity, accuracy).
        prompt_template (str): Jinja template to use.

    Returns:
        dict: Evaluation result with scores and justification.
    """
    variant_data = [_build_variant_entry(node_id=node_id, graph=graph, config=config) 
                    for node_id in node_ids]

    variables = {
        "goal": goal,
        "variants": variant_data,
    }

    # Raw render and completion (no memory graph logging)
    prompt_path = get_prompt_path(config, name=prompt_template)
    prompt = render_template(prompt_path, template_vars=variables)
    provider = get_llm_provider(config)
    response = provider.generate(prompt=prompt)

    # TODO: add optional logging using llm_run_and_store() for evaluation tracking
    return extract_first_json_block(response)
