from typing import Optional, Dict, Any, Callable, List
from pathlib import Path

from cybermule.utils.config_loader import get_prompt_path
from cybermule.utils.template_utils import render_template
from cybermule.providers.llm_provider import get_llm_provider
from cybermule.memory.history_utils import extract_chat_history
from cybermule.memory.memory_graph import MemoryGraph
from cybermule.version_info import get_version_info


def log_llm_task(
    graph: MemoryGraph,
    node_id: str,
    prompt_template: str,
    prompt: str,
    response: str,
    **extra,
) -> None:
    """
    Log a full LLM task interaction to the memory graph with metadata.

    Args:
        graph: MemoryGraph instance
        node_id: ID of the node being updated
        prompt_template: Name of the template used (e.g., "review_git_commit.j2")
        prompt: Final rendered prompt string
        response: LLM response string
        extra: Any additional metadata (e.g., status, commit_sha)
    """
    version_info = get_version_info()
    graph.update(
        node_id,
        prompt=prompt,
        response=response,
        prompt_template=prompt_template,
        cybermule_commit=version_info.get("git_commit"),
        **extra
    )


def run_llm_task(
    config: dict,
    graph: MemoryGraph,
    node_id: str,
    prompt_template: str,
    variables: dict,
    respond_prefix: Optional[str] = None,
    status: str = "COMPLETED",
    tags: Optional[List[str]] = None,
    extra: Optional[dict] = None,
) -> str:
    """
    Execute an LLM task using a prompt template, log the result to the memory graph.

    Args:
        config: Global configuration dictionary
        graph: MemoryGraph instance
        node_id: Target node in the graph
        prompt_template: Template name (e.g., "summarize_traceback.j2")
        variables: Dict of values to render into the template
        respond_prefix: Optional prefix to prepend to LLM input
        status: Task completion status to store in the graph
        tags: Optional list of tags for the memory node
        extra: Additional metadata to log in the graph

    Returns:
        LLM-generated response text
    """
    prompt_path = get_prompt_path(config, name=prompt_template)
    prompt = render_template(Path(prompt_path), template_vars=variables)

    llm = get_llm_provider(config)
    history = extract_chat_history(graph.parent_id_of(node_id), memory=graph)
    response = llm.generate(prompt, history=history, respond_prefix=respond_prefix)

    extra = extra or {}

    log_llm_task(
        graph=graph,
        node_id=node_id,
        prompt_template=prompt_template,
        prompt=prompt,
        response=response,
        status=status,
        tags=tags,
        **extra,
    )

    return response


def run_llm_and_store(
    *,
    config: dict,
    graph: MemoryGraph,
    node_id: str,
    prompt_template: str,
    variables: dict,
    postprocess: Callable[[str], Dict[str, Any]],
    status: str = "COMPLETED",
    tags: Optional[List[str]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Run an LLM task and store derived metadata (e.g. parsed JSON) back into the memory graph.

    This is a higher-level wrapper around `run_llm_task()` for workflows that extract
    structured output from the LLM response and want to log it to the memory graph.

    Args:
        config: Configuration for the LLM provider
        graph: MemoryGraph instance
        node_id: The graph node to attach all logs to
        prompt_template: Jinja template filename
        variables: Variables for template rendering
        postprocess: Function to extract structured info from LLM response (e.g. JSON block)
        status: Status string to store with the response (e.g. "SUMMARIZED", "FIX_ATTEMPT_1")
        tags: Optional tags for graph node
        extra: Optional additional metadata to log

    Returns:
        Raw LLM response string (unmodified)
    """
    response = run_llm_task(
        config=config,
        graph=graph,
        node_id=node_id,
        prompt_template=prompt_template,
        variables=variables,
        status=status,
        tags=tags,
        extra=extra,
    )

    derived_metadata = postprocess(response)
    graph.update(node_id, **derived_metadata)

    return response, derived_metadata
