import json
import uuid
from pathlib import Path
import networkx as nx

class MemoryGraph:
    def __init__(self, storage_path="memory_graph.json"):
        self.storage_path = Path(storage_path)
        self.graph = nx.DiGraph()  # Directed graph for parent-child relationships
        if self.storage_path.exists():
            self._load()

    def _load(self):
        """Load graph data from JSON file and reconstruct NetworkX graph."""
        with open(self.storage_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Clear existing graph
        self.graph.clear()
        
        # Add all nodes first
        for node_id, node_data in data.items():
            # Remove 'children' from node attributes as NetworkX handles edges separately
            node_attrs = {k: v for k, v in node_data.items() if k != 'children'}
            self.graph.add_node(node_id, **node_attrs)
        
        # Add edges based on parent-child relationships
        for node_id, node_data in data.items():
            parent_id = node_data.get('parent')
            if parent_id and parent_id in data:
                # Add edge from parent to child
                self.graph.add_edge(parent_id, node_id)

    def _save(self):
        """Save NetworkX graph to JSON file in the original format."""
        data = {}
        
        for node_id in self.graph.nodes():
            # Get node attributes
            node_attrs = dict(self.graph.nodes[node_id])
            
            # Get children (successors in directed graph)
            children = list(self.graph.successors(node_id))
            node_attrs['children'] = children
            
            # Ensure parent is set correctly
            parents = list(self.graph.predecessors(node_id))
            node_attrs['parent'] = parents[0] if parents else None
            
            data[node_id] = node_attrs
        
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def new(self, task, parent_id=None):
        """Create a new node with optional parent relationship."""
        node_id = str(uuid.uuid4())
        
        # Create node with default attributes
        node_attrs = {
            "id": node_id,
            "task": task,
            "prompt": "",
            "response": "",
            "status": "PENDING",
            "error": "",
            "parent": parent_id
        }
        
        # Add node to graph
        self.graph.add_node(node_id, **node_attrs)
        
        # Add edge if parent exists
        if parent_id and parent_id in self.graph:
            self.graph.add_edge(parent_id, node_id)
        
        self._save()
        return node_id

    def update(self, node_id, **kwargs):
        """Update node attributes."""
        if node_id not in self.graph:
            raise KeyError(f"Node {node_id} not found.")
        
        # Update node attributes
        for key, value in kwargs.items():
            self.graph.nodes[node_id][key] = value
        
        self._save()

    def get(self, node_id):
        """Get a single node with its attributes and relationships."""
        if node_id not in self.graph:
            return None
        
        # Get node attributes
        node_data = dict(self.graph.nodes[node_id])
        
        # Add relationship information
        node_data['children'] = list(self.graph.successors(node_id))
        parents = list(self.graph.predecessors(node_id))
        node_data['parent'] = parents[0] if parents else None
        
        return node_data

    def list(self):
        """Get all nodes with their attributes and relationships."""
        nodes = []
        for node_id in self.graph.nodes():
            node_data = self.get(node_id)
            nodes.append(node_data)
        return nodes

    def children_of(self, node_id):
        """Get all children nodes of the specified node."""
        if node_id not in self.graph:
            return []
        
        children = []
        for child_id in self.graph.successors(node_id):
            child_data = self.get(child_id)
            children.append(child_data)
        
        return children

    def parent_of(self, node_id):
        """Get the parent node of the specified node."""
        if node_id not in self.graph:
            return None
        
        parents = list(self.graph.predecessors(node_id))
        if not parents:
            return None
        
        parent_id = parents[0]
        return self.get(parent_id)

    # Additional NetworkX-powered methods that could be useful
    
    def get_descendants(self, node_id):
        """Get all descendants (recursive children) of a node."""
        if node_id not in self.graph:
            return []
        
        descendants = []
        for desc_id in nx.descendants(self.graph, node_id):
            descendants.append(self.get(desc_id))
        
        return descendants

    def get_ancestors(self, node_id):
        """Get all ancestors (recursive parents) of a node."""
        if node_id not in self.graph:
            return []
        
        ancestors = []
        for anc_id in nx.ancestors(self.graph, node_id):
            ancestors.append(self.get(anc_id))
        
        return ancestors

    def get_path_to_root(self, node_id):
        """Get the path from node to root (node with no parent)."""
        if node_id not in self.graph:
            return []
        
        path = [node_id]
        current = node_id
        
        while True:
            parents = list(self.graph.predecessors(current))
            if not parents:
                break
            current = parents[0]
            path.append(current)
        
        # Return path with node data
        return [self.get(nid) for nid in reversed(path)]

    def is_valid_graph(self):
        """Check if the graph is a valid tree/forest (no cycles)."""
        return nx.is_forest(self.graph)

    def get_roots(self):
        """Get all root nodes (nodes with no parents)."""
        roots = []
        for node_id in self.graph.nodes():
            if self.graph.in_degree(node_id) == 0:
                roots.append(self.get(node_id))
        
        return roots

    def get_leaves(self):
        """Get all leaf nodes (nodes with no children)."""
        leaves = []
        for node_id in self.graph.nodes():
            if self.graph.out_degree(node_id) == 0:
                leaves.append(self.get(node_id))
        
        return leaves
