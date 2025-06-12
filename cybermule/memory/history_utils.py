from typing import List, Dict, Optional, Union
from cybermule.memory.memory_graph import MemoryGraph

def extract_chat_history(
    node: Optional[Union[str, dict]],
    memory: MemoryGraph,
    include_root: bool = True
) -> List[Dict]:
    """
    Traverse the ancestry of a node in the MemoryGraph and return a Claude-style
    chat history as a list of messages suitable for LLM context.

    Each node contributes up to two messages:
        - A "user" message from the 'prompt'
        - An "assistant" message from the 'response'

    Args:
        node: Node ID (str) or node dict from MemoryGraph.
        memory: The MemoryGraph instance to use.
        include_root: If False, excludes the final node (assumed current step).

    Returns:
        List of messages, e.g.:
        [
            {"role": "user", "content": [{"type": "text", "text": "..." }]},
            {"role": "assistant", "content": [{"type": "text", "text": "..." }]},
            ...
        ]
    """
    if not node:
        return []

    if isinstance(node, dict):
        node_id = node["id"]
    else:
        node_id = node

    path = memory.get_path_to_root(node_id)
    if not include_root:
        path = path[:-1]

    history = []
    for n in path:
        prompt = n.get("prompt", "").strip()
        response = n.get("response", "").strip()

        if prompt:
            history.append({
                "role": "user",
                "content": [{"type": "text", "text": prompt}]
            })

        if response:
            history.append({
                "role": "assistant",
                "content": [{"type": "text", "text": response}]
            })

    return history

def format_chat_history_as_text(messages: List[dict]) -> str:
    lines = []
    for msg in messages:
        role = msg["role"]
        content_chunks = msg["content"]
        for chunk in content_chunks:
            text = chunk.get("text", "")
            lines.append(f"{role.upper()}: {text.strip()}")
    return "\n\n".join(lines)
