import networkx as nx

def get_descendants(graph, node_id):
    return list(nx.descendants(graph, node_id)) if node_id in graph else []

def get_ancestors(graph, node_id):
    return list(nx.ancestors(graph, node_id)) if node_id in graph else []

def get_path_to_root(graph, node_id):
    path = []
    current = node_id
    while current in graph:
        path.append(current)
        preds = list(graph.predecessors(current))
        if not preds:
            break
        current = preds[0]
    return list(reversed(path))

def get_roots(graph):
    return [n for n in graph.nodes if graph.in_degree(n) == 0]

def get_leaves(graph):
    return [n for n in graph.nodes if graph.out_degree(n) == 0]

def is_valid_graph(graph):
    return nx.is_forest(graph)
