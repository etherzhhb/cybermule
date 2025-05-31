import json

def load_graph_from_file(graph, storage_path):
    if not storage_path.exists() or storage_path.stat().st_size == 0:
        return

    with open(storage_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    graph.clear()
    for node_id, attrs in data.items():
        node_attrs = {k: v for k, v in attrs.items() if k != "children"}
        graph.add_node(node_id, **node_attrs)

    for node_id, attrs in data.items():
        parent_id = attrs.get("parent")
        if parent_id and parent_id in data:
            graph.add_edge(parent_id, node_id)

def save_graph_to_file(graph, storage_path):
    data = {}
    for node_id in graph.nodes():
        attrs = dict(graph.nodes[node_id])
        attrs["children"] = list(graph.successors(node_id))
        parents = list(graph.predecessors(node_id))
        attrs["parent"] = parents[0] if parents else None
        data[node_id] = attrs

    with open(storage_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
