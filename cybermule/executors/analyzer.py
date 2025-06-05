from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

from cybermule.providers.llm_provider import get_llm_provider
from cybermule.memory.memory_graph import MemoryGraph
from cybermule.symbol_resolution import (
    resolve_symbol,
    resolve_symbol_in_function,
    extract_definition_by_callsite,
)

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
    try:
        error_summary, = extract_tagged_blocks(response, tag="error_summary")
    except ValueError:
        raise RuntimeError("LLM didnt respond with error_summary")

    local_graph.update(node_id, prompt=prompt, response=response, 
                       error_summary=error_summary, status="SUMMARIZED")

    return error_summary, node_id if graph else None


def fulfill_context_requests(required_info: List[Dict], project_root: Path) -> List[Dict]:
    """
    Resolve all LLM context requests to symbol definitions.
    Priority:
      1. ref_path + ref_function + symbol → resolve_symbol_in_function
      2. ref_path + lineno + symbol → extract_definition_by_callsite
      3. symbol → resolve_symbol
    Returns a list of context dicts: {file, symbol, snippet, start_line, traceback_line}
    """

    results = []

    for info in required_info:
        symbol = info.get("symbol")
        ref_path = info.get("ref_path")
        ref_function = info.get("ref_function")
        lineno = info.get("lineno")
        result = None

        # Strategy 1: Use ref_function inside known file
        if symbol and ref_path and ref_function:
            result = resolve_symbol_in_function(
                ref_path=Path(ref_path),
                ref_function=ref_function,
                symbol=symbol,
                project_root=project_root,
            )

        # Strategy 2: Use callsite line number
        if result is None and symbol and ref_path and lineno:
            result = extract_definition_by_callsite(
                path=Path(ref_path),
                line=lineno,
                symbol=symbol,
                project_root=project_root,
            )

        # Strategy 3: Fallback: global symbol resolution
        if result is None and symbol:
            result = resolve_symbol(symbol=symbol, project_root=project_root)

        if result:
            result.update({
                "traceback_line": lineno or result.get("start_line"),
            })
            results.append(result)

    return results


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

    project_root = Path(config.get("project_root", "."))

    current_contexts = base_contexts[:]
    node_id = graph.new("Generate fix plan", parent_id=parent_id, tags=["fix"])
    history = extract_chat_history(parent_id, memory=graph)
    llm = get_llm_provider(config)

    for round_num in range(max_rounds):
        prompt_path = get_prompt_path(config, "generate_fix_from_summary.j2")
        prompt = render_template(Path(prompt_path), {
            "ERROR_SUMMARY": error_summary,
            "CODE_CONTEXTS": current_contexts
        })

        response = llm.generate(prompt, history=history, respond_prefix='error_analysis')
        fix_plan = extract_first_json_block(response)

        # Log current reasoning step
        graph.update(node_id, prompt=prompt, response=response,
                     status=f"FIX_ATTEMPT_{round_num + 1}", fix_plan=fix_plan)

        needs_more = fix_plan.get("needs_more_context", False)
        required_info = fix_plan.get("required_info", [])

        if not needs_more or not required_info:
            graph.update(node_id, status="FIX_FINALIZED", fix_plan=fix_plan)
            return fix_plan, node_id

        # Fulfill LLM's request for more symbol context
        current_contexts.extend(fulfill_context_requests(
            required_info=required_info,
            project_root=project_root
        ))

    # Return last attempt even if not finalized
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