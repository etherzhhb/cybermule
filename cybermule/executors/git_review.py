from typing import Optional, Tuple

from cybermule.executors.llm_runner import llm_run
from cybermule.utils import git_utils
from cybermule.memory.memory_graph import MemoryGraph


def review_commit_with_llm(
    config: dict,
    graph: Optional[MemoryGraph] = None,
    parent_id: Optional[str] = None,
    sha: Optional[str] = None,
    fetch: Optional[str] = None,
) -> Tuple[str, str]:
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
    

    review, node_id = llm_run(
        config=config,
        graph=graph,
        title=f"Review commit {commit_sha[:7]}",
        parent_id=parent_id, 
        tags=["review"],
        prompt_template="review_git_commit.j2",
        variables={
            "commit_message": commit_msg,
            "commit_diff": commit_diff
        },
        status="REVIEWED",
        extra={"commit_sha": commit_sha}
    )

    return review, node_id
