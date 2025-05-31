import uuid
from pathlib import Path
import networkx as nx

from cybermule.memory.graph_utils import (
    get_descendants, get_ancestors, get_path_to_root,
    get_roots, get_leaves, is_valid_graph
)
from cybermule.memory.storage import load_graph_from_file, save_graph_to_file

class MemoryGraph:
    def __init__(self, storage_path="memory_graph.json"):
        self.storage_path = Path(storage_path)
        self.graph = nx.DiGraph()
        load_graph_from_file(self.graph, self.storage_path)

    def _save(self):
        save_graph_to_file(self.graph, self.storage_path)

    def new(self, task, parent_id=None):
        node_id = str(uuid.uuid4())
        self.graph.add_node(node_id, id=node_id, task=task,
                            prompt="", response="", status="PENDING", error="", parent=parent_id)
        if parent_id and parent_id in self.graph:
            self.graph.add_edge(parent_id, node_id)
        self._save()
        return node_id

    def update(self, node_id, **kwargs):
        if node_id not in self.graph:
            raise KeyError(f"Node {node_id} not found.")
        self.graph.nodes[node_id].update(kwargs)
        self._save()

    def get(self, node_id):
        if node_id not in self.graph:
            return None
        node = dict(self.graph.nodes[node_id])
        node["children"] = list(self.graph.successors(node_id))
        preds = list(self.graph.predecessors(node_id))
        node["parent"] = preds[0] if preds else None
        return node

    def list(self):
        return [self.get(nid) for nid in self.graph.nodes]

    def children_of(self, node_id):
        return [self.get(cid) for cid in self.graph.successors(node_id)]

    def parent_of(self, node_id):
        preds = list(self.graph.predecessors(node_id))
        return self.get(preds[0]) if preds else None

    def get_descendants(self, node_id):
        return [self.get(nid) for nid in get_descendants(self.graph, node_id)]

    def get_ancestors(self, node_id):
        return [self.get(nid) for nid in get_ancestors(self.graph, node_id)]

    def get_path_to_root(self, node_id):
        return [self.get(nid) for nid in get_path_to_root(self.graph, node_id)]

    def get_roots(self):
        return [self.get(nid) for nid in get_roots(self.graph)]

    def get_leaves(self):
        return [self.get(nid) for nid in get_leaves(self.graph)]

    def is_valid_graph(self):
        return is_valid_graph(self.graph)
