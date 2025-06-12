from cybermule.executors.llm_runner import run_llm_task
from cybermule.memory.graph_utils import get_descendants

def replay_subtree(root_node_id, graph, config, prompt_substitutions=None, tag="REPLAYED"):
    """
    Replays a subtree of LLM tasks starting from root_node_id using the same or updated prompt templates.

    Args:
        root_node_id (str): ID of the root node to replay.
        graph (MemoryGraph): The memory graph instance.
        config (dict): Global config for LLM execution.
        prompt_substitutions (dict): Optional map {original_prompt_name: new_prompt_name}.
        tag (str): Tag to apply to replayed nodes.

    Returns:
        dict: Mapping of original node IDs to new replayed node IDs.
    """
    prompt_substitutions = prompt_substitutions or {}
    all_nodes = [root_node_id] + sorted(
        get_descendants(graph.graph, root_node_id),
        key=lambda nid: graph.graph.nodes[nid].get("timestamp", "")
    )

    node_id_map = {}

    for original_id in all_nodes:
        original = graph.get(original_id)
        parent_id = original.get("parent")
        new_parent_id = node_id_map.get(parent_id) if parent_id else None

        task_name = original.get("task")
        original_prompt = original.get("prompt_template")
        new_prompt = prompt_substitutions.get(original_prompt, original_prompt)
        variables = original.get("variables", {})  # requires original run to store this

        new_node_id = graph.new(
            task=task_name,
            parent_id=new_parent_id,
            tags=[tag],
            mode="REPLAY"
        )

        _ = run_llm_task(
            config=config,
            graph=graph,
            node_id=new_node_id,
            prompt_template=new_prompt,
            variables=variables,
            status="COMPLETED",
            tags=[tag],
            extra={
                "replay_of": original_id,
                "prompt_variant_of": original_prompt if new_prompt != original_prompt else None
            }
        )

        node_id_map[original_id] = new_node_id

    return node_id_map
