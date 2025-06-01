from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import json

from cybermule.providers.llm_provider import get_llm_provider
from cybermule.memory.memory_graph import MemoryGraph
from cybermule.utils.template_utils import render_template
from cybermule.utils.config_loader import get_prompt_path
from cybermule.utils.parsing import extract_first_json_block
from cybermule.memory.history_utils import extract_chat_history


def summarize_traceback(
    traceback: str,
    config: Dict[str, Any],
    graph: Optional[MemoryGraph] = None,
    parent_id: Optional[str] = None
) -> Tuple[str, Optional[str]]:
    """
    Use an LLM to summarize the traceback into a natural language explanation.

    Returns:
        (summary: str, node_id: Optional[str])
    """
    prompt_path = get_prompt_path(config, "summarize_traceback.j2")
    prompt = render_template(Path(prompt_path), {"traceback": traceback})

    local_graph = graph or MemoryGraph()
    node_id = local_graph.new("Summarize traceback", parent_id=parent_id, tags=["traceback"])

    if parent_id:
        history = extract_chat_history(parent_id, graph)
    else:
        history = ()

    llm = get_llm_provider(config)
    response = llm.generate(prompt, history=history)

    local_graph.update(node_id, prompt=prompt, response=response, status="SUMMARIZED")

    return response, node_id if graph else None


def generate_fix_from_summary(
    config: Dict[str, Any],
    graph: Optional[MemoryGraph],
    parent_id: Optional[str]
) -> Tuple[dict, Optional[str]]:
    """
    Use an LLM to generate a structured code fix plan from a summary.

    Returns:
        (fix_plan: dict, node_id: Optional[str])
    """
    prompt_path = get_prompt_path(config, "generate_fix_from_summary.j2")
    prompt = render_template(Path(prompt_path), {"summary": ''})

    node_id = graph.new("Generate fix plan", parent_id=parent_id, tags=["fix"])

    history = extract_chat_history(parent_id, graph)

    llm = get_llm_provider(config)
    response = llm.generate(prompt, history=history)

    fix_plan = extract_first_json_block(response) or json.loads(response)

    graph.update(node_id, prompt=prompt, response=response,
                  status="FIX_GENERATED", fix_plan=fix_plan)

    return fix_plan, node_id


def analyze_failure_with_llm(
    traceback: str,
    config: Dict[str, Any],
    graph: Optional[MemoryGraph] = None,
    parent_id: Optional[str] = None
) -> dict:
    """
    Orchestrates traceback summarization and fix generation.

    Returns:
        fix_plan: dict
    """
    local_graph = graph or MemoryGraph()

    # Step 1: Summarize
    summary, summary_node = summarize_traceback(
        traceback, config, graph=local_graph, parent_id=parent_id
    )

    # Step 2: Generate fix
    fix_plan, node_id = generate_fix_from_summary(
        config=config, graph=local_graph, parent_id=summary_node
    )

    return fix_plan, node_id if graph else None
