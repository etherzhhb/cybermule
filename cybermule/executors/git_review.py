from typing import Optional, Tuple
from pathlib import Path

from cybermule.memory.history_utils import extract_chat_history
from cybermule.utils import git_utils
from cybermule.utils.config_loader import get_prompt_path
from cybermule.providers.llm_provider import get_llm_provider
from cybermule.memory.memory_graph import MemoryGraph
from langchain.prompts import PromptTemplate


def review_commit_with_llm(
    config: dict,
    graph: Optional[MemoryGraph] = None,
    parent_id: Optional[str] = None,
    sha: Optional[str] = None,
    fetch: Optional[str] = None,
) -> Tuple[str, str, str]:
    """
    Run LLM-based review of a Git commit and log it to the MemoryGraph.

    Args:
        config: Global configuration dictionary
        sha: Specific commit SHA to review (default: latest)
        fetch: Optional Git remote to fetch before reviewing

    Returns:
        (memory_node_id, prompt_used, review_text)
    """
    if fetch:
        git_utils.fetch_remote(fetch)

    commit_sha = sha or git_utils.get_latest_commit_sha()
    commit_msg = git_utils.get_commit_message_by_sha(commit_sha)
    commit_diff = git_utils.get_commit_diff_by_sha(commit_sha)
    
    local_graph = graph or MemoryGraph()

    # Create a memory node for traceability
    node_id = local_graph.new(f"Review commit {commit_sha[:7]}", parent_id=parent_id, tags=["review"])

    # Load prompt template and format it
    prompt_path = get_prompt_path(config, name="review_git_commit.prompt")
    prompt_template = PromptTemplate.from_template(prompt_path.read_text())
    prompt = prompt_template.format(commit_message=commit_msg, commit_diff=commit_diff)

    # LLM call
    llm = get_llm_provider(config)
    
    history = extract_chat_history(parent_id, memory=local_graph)
    review = llm.generate(prompt, history=history)

    # Log to graph
    local_graph.update(node_id, prompt=prompt, response=review, status="REVIEWED")

    return review, node_id if graph else None
