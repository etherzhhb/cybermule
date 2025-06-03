from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import json

import typer

from cybermule.providers.llm_provider import get_llm_provider
from cybermule.memory.memory_graph import MemoryGraph
from cybermule.symbol_resolution import extract_definition_by_callsite, resolve_symbol
from cybermule.utils.context_extract import (
    extract_locations,
    get_context_snippets,
)
from cybermule.utils.template_utils import render_template
from cybermule.utils.config_loader import get_prompt_path
from cybermule.utils.parsing import extract_first_json_block, extract_tagged_blocks
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
    prompt = render_template(Path(prompt_path), {"TRACEBACK": traceback})

    local_graph = graph or MemoryGraph()
    node_id = local_graph.new("Summarize traceback", parent_id=parent_id, tags=["traceback"])

    llm = get_llm_provider(config)
    history = extract_chat_history(parent_id, memory=local_graph)
    response = llm.generate(prompt, history=history)
    error_summary, = extract_tagged_blocks(response, tag="error_summary")

    local_graph.update(node_id, prompt=prompt, response=response, 
                       error_summary=error_summary, status="SUMMARIZED")

    return error_summary, node_id if graph else None


def fulfill_context_requests(
    request_info: list,
    context_map: Dict[str, Dict],
    current_contexts: list,
    project_root: Optional[Path] = None
) -> None:
    """
    Extract additional code snippets requested by the LLM, based on symbol or callsite info.
    Avoids duplicating context already present in context_map.
    """
    project_root = project_root or Path(".").resolve()

    for request in request_info:
        context_id = request.get("code_context_id")  # e.g., "some/file.py:42"
        symbol = request.get("symbol")

        try:
            parts = context_id.split(":")
            path = Path(parts[0])
            line = int(parts[1]) if len(parts) > 1 else None

            ctx = None

            if symbol and line is None:
                ctx = resolve_symbol(symbol, project_root=project_root)
            elif symbol:
                ctx = extract_definition_by_callsite(path, line, project_root=project_root)

            if not ctx:
                typer.echo(f"⚠️  [WARN] Could not extract symbol definition for: {request}")
                continue

            key = f"{ctx['file']}:{ctx['start_line']}"
            if key not in context_map:
                context_map[key] = ctx
                current_contexts.append(ctx)

        except Exception as e:
            typer.echo(f"💥 [ERROR] Failed to fulfill context request: {request} → {e}")


def generate_fix_from_summary(
    error_summary: str,
    traceback: str,
    config: Dict[str, Any],
    graph: Optional[MemoryGraph],
    parent_id: Optional[str],
    max_rounds: int = 3
) -> Tuple[dict, Optional[str]]:
    """
    Use an LLM to generate a structured code fix plan, retrying if more context is requested.

    Returns:
        (fix_plan: dict, node_id: Optional[str])
    """
    base_locations = extract_locations(traceback)
    base_contexts = get_context_snippets(base_locations)
    context_map = {
        f"{ctx['file']}:{ctx['traceback_line']}": ctx for ctx in base_contexts
    }

    project_root = Path(config.get("project_root", "."))

    current_contexts = base_contexts[:]
    node_id = graph.new("Generate fix plan", parent_id=parent_id, tags=["fix"])
    history = () #extract_chat_history(parent_id, graph)
    llm = get_llm_provider(config)

    for round_num in range(max_rounds):
        prompt_path = get_prompt_path(config, "generate_fix_from_summary.j2")
        prompt = render_template(Path(prompt_path), {
            "ERROR_SUMMARY": error_summary,
            "CODE_CONTEXTS": current_contexts
        })

        response = llm.generate(prompt, history=history, respond_prefix='error_analysis')
        fix_plan = extract_first_json_block(response)

        graph.update(node_id, prompt=prompt, response=response,
                     status=f"FIX_ATTEMPT_{round_num + 1}", fix_plan=fix_plan)

        request_info = fix_plan.get("required_info", [])
        if not request_info:
            return fix_plan, node_id

        fulfill_context_requests(request_info=request_info, context_map=context_map,
                                 current_contexts=current_contexts,
                                 project_root=project_root)

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
    error_summary, summary_node = summarize_traceback(
        traceback, config=config, graph=local_graph, parent_id=parent_id
    )

    # Step 2: Generate fix
    fix_plan, node_id = generate_fix_from_summary(
        error_summary=error_summary, traceback=traceback, config=config, 
        graph=local_graph, parent_id=summary_node
    )

    return fix_plan, node_id if graph else None