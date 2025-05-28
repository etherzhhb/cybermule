import json
import uuid
from pathlib import Path

class MemoryGraph:
    def __init__(self, storage_path="memory_graph.json"):
        self.storage_path = Path(storage_path)
        self._data = {}  # node_id -> node dict
        if self.storage_path.exists():
            self._load()

    def _load(self):
        with open(self.storage_path, "r", encoding="utf-8") as f:
            self._data = json.load(f)

    def _save(self):
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    def new(self, task, parent_id=None):
        node_id = str(uuid.uuid4())
        node = {
            "id": node_id,
            "task": task,
            "prompt": "",
            "response": "",
            "status": "PENDING",
            "error": "",
            "parent": parent_id,
            "children": []
        }
        self._data[node_id] = node
        if parent_id and parent_id in self._data:
            self._data[parent_id]["children"].append(node_id)
        self._save()
        return node_id

    def update(self, node_id, **kwargs):
        if node_id not in self._data:
            raise KeyError(f"Node {node_id} not found.")
        self._data[node_id].update(kwargs)
        self._save()

    def get(self, node_id):
        return self._data.get(node_id)

    def list(self):
        return list(self._data.values())

    def children_of(self, node_id):
        node = self._data.get(node_id)
        return [self._data[cid] for cid in node["children"]] if node else []

    def parent_of(self, node_id):
        node = self._data.get(node_id)
        return self._data.get(node["parent"]) if node and node["parent"] else None