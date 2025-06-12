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
