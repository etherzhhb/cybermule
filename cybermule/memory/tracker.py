from typing import Optional, Dict, Any
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
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log a full LLM task interaction to the memory graph with metadata.

    Args:
        graph: MemoryGraph instance
        node_id: ID of the node being updated
        prompt_template: Name of the template used (e.g., "review_git_commit.prompt")
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
        **(extra or {})
    )


def run_llm_task(
    config: dict,
    graph: MemoryGraph,
    node_id: str,
    prompt_template: str,
    variables: dict,
    parent_id: Optional[str] = None,
    respond_prefix: Optional[str] = None,
    status: str = "COMPLETED",
    tags: Optional[list] = None,
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
        respond_prefix: Optional string for LLM generation behavior
        status: Task completion status (default: "COMPLETED")
        tags: Optional list of tags to attach
        extra: Extra metadata for logging

    Returns:
        LLM-generated response text
    """
    prompt_path = get_prompt_path(config, name=prompt_template)
    prompt = render_template(Path(prompt_path), template_vars=variables)

    llm = get_llm_provider(config)
    history = extract_chat_history(parent_id, memory=graph) if parent_id else None
    response = llm.generate(prompt, history=history, respond_prefix=respond_prefix)

    log_llm_task(
        graph=graph,
        node_id=node_id,
        prompt_template=prompt_template,
        prompt=prompt,
        response=response,
        extra={**(extra or {}), "status": status, "tags": tags or []},
    )

    return response
