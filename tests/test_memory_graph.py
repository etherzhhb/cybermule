import os
import tempfile
import pytest
from cybermule.memory.memory_graph import MemoryGraph

@pytest.fixture
def temp_graph_file():
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        yield tf.name
    os.remove(tf.name)

def test_create_and_retrieve_node(temp_graph_file):
    mg = MemoryGraph(storage_path=temp_graph_file)
    node_id = mg.new("Test Task")
    node = mg.get(node_id)
    assert node["id"] == node_id
    assert node["task"] == "Test Task"
    assert node["status"] == "PENDING"
    assert node["parent"] is None
    assert node["children"] == []

def test_parent_child_relationship(temp_graph_file):
    mg = MemoryGraph(storage_path=temp_graph_file)
    parent_id = mg.new("Parent Task")
    child_id = mg.new("Child Task", parent_id=parent_id)
    parent = mg.get(parent_id)
    child = mg.get(child_id)
    assert child["parent"] == parent_id
    assert child_id in parent["children"]

def test_update_node(temp_graph_file):
    mg = MemoryGraph(storage_path=temp_graph_file)
    node_id = mg.new("Task to Update")
    mg.update(node_id, status="SUCCESS", prompt="Q", response="A")
    node = mg.get(node_id)
    assert node["status"] == "SUCCESS"
    assert node["prompt"] == "Q"
    assert node["response"] == "A"

def test_list_nodes(temp_graph_file):
    mg = MemoryGraph(storage_path=temp_graph_file)
    id1 = mg.new("Task 1")
    id2 = mg.new("Task 2")
    nodes = mg.list()
    ids = [n["id"] for n in nodes]
    assert id1 in ids
    assert id2 in ids

def test_graph_structure(temp_graph_file):
    mg = MemoryGraph(storage_path=temp_graph_file)
    root_id = mg.new("Root")
    child1_id = mg.new("Child1", parent_id=root_id)
    child2_id = mg.new("Child2", parent_id=child1_id)
    assert mg.is_valid_graph()
    path = mg.get_path_to_root(child2_id)
    assert [n["id"] for n in path] == [root_id, child1_id, child2_id]

def test_descendants_and_ancestors(temp_graph_file):
    mg = MemoryGraph(storage_path=temp_graph_file)
    root_id = mg.new("Root")
    mid_id = mg.new("Mid", parent_id=root_id)
    leaf_id = mg.new("Leaf", parent_id=mid_id)

    descendants = mg.get_descendants(root_id)
    descendant_ids = [n["id"] for n in descendants]
    assert mid_id in descendant_ids
    assert leaf_id in descendant_ids

    ancestors = mg.get_ancestors(leaf_id)
    ancestor_ids = [n["id"] for n in ancestors]
    assert mid_id in ancestor_ids
    assert root_id in ancestor_ids

def test_get_leaves_and_roots(temp_graph_file):
    mg = MemoryGraph(storage_path=temp_graph_file)
    root1 = mg.new("Root1")
    root2 = mg.new("Root2")
    leaf1 = mg.new("Leaf1", parent_id=root1)
    leaf2 = mg.new("Leaf2", parent_id=root1)

    roots = mg.get_roots()
    root_ids = [n["id"] for n in roots]
    assert root1 in root_ids
    assert root2 in root_ids

    leaves = mg.get_leaves()
    leaf_ids = [n["id"] for n in leaves]
    assert leaf1 in leaf_ids
    assert leaf2 in leaf_ids

def test_new_node_metadata(temp_graph_file):
    from datetime import datetime
    mg = MemoryGraph(storage_path=temp_graph_file)
    node_id = mg.new("Task", tags=["test", "debug"], mode="planner-loop")
    node = mg.get(node_id)
    assert "timestamp" in node
    assert "T" in node["timestamp"] and node["timestamp"].endswith("Z")
    assert node["tags"] == ["test", "debug"]
    assert node["mode"] == "planner-loop"
