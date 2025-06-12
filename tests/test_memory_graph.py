import os
import tempfile
import pytest
from cybermule.memory.memory_graph import MemoryGraph
from cybermule.memory.history_utils import extract_chat_history, format_chat_history_as_text

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
    mg = MemoryGraph(storage_path=temp_graph_file)
    node_id = mg.new("Task", tags=["test", "debug"], mode="planner-loop")
    node = mg.get(node_id)
    assert "timestamp" in node
    assert "T" in node["timestamp"] and node["timestamp"].endswith("Z")
    assert node["tags"] == ["test", "debug"]
    assert node["mode"] == "planner-loop"

def test_extract_chat_history_from_memory_graph(temp_graph_file):
    mg = MemoryGraph(storage_path=temp_graph_file)

    # Create a 3-node ancestry chain: root → mid → leaf
    root_id = mg.new("Root")
    mg.update(root_id, prompt="prompt 1", response="response 1")

    mid_id = mg.new("Mid", parent_id=root_id)
    mg.update(mid_id, prompt="prompt 2", response="response 2")

    leaf_id = mg.new("Leaf", parent_id=mid_id)
    mg.update(leaf_id, prompt="prompt 3", response="response 3")

    # --- Case 1: include_root=True
    history = extract_chat_history(leaf_id, mg, include_root=True)

    assert len(history) == 6
    assert history[0]["role"] == "user" and history[0]["content"][0]["text"] == "prompt 1"
    assert history[1]["role"] == "assistant" and history[1]["content"][0]["text"] == "response 1"
    assert history[-1]["content"][0]["text"] == "response 3"

    # --- Case 2: include_root=False
    history_without_leaf = extract_chat_history(leaf_id, mg, include_root=False)

    assert len(history_without_leaf) == 4
    assert history_without_leaf[-1]["content"][0]["text"] == "response 2"

    # --- Case 3: skip nodes with empty prompt/response
    empty_id = mg.new("Empty", parent_id=leaf_id)  # no update → no prompt/response
    history_with_empty = extract_chat_history(empty_id, mg, include_root=True)

    assert len(history_with_empty) == 6  # Empty node adds nothing

def test_format_chat_history_as_text_simple():
    messages = [
        {"role": "user", "content": [{"text": "What is 2+2?"}]},
        {"role": "assistant", "content": [{"text": "4"}]},
        {"role": "user", "content": [{"text": "Explain why."}]},
        {"role": "assistant", "content": [{"text": "Because 2 plus 2 equals 4."}]},
    ]

    result = format_chat_history_as_text(messages)
    assert "USER: What is 2+2?" in result
    assert "ASSISTANT: 4" in result
    assert "USER: Explain why." in result
    assert "ASSISTANT: Because 2 plus 2 equals 4." in result

    # Optional: check structure
    lines = [line for line in result.strip().splitlines() if line.strip()]
    assert lines[0].startswith("USER:")
    assert lines[1].startswith("ASSISTANT:")
