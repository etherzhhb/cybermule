# File: tests/test_llm_replay.py

import pytest
from pathlib import Path
from cybermule.executors.llm_replay import replay_subtree
from cybermule.memory.memory_graph import MemoryGraph
from cybermule.utils import template_utils

class DummyLLMRunner:
    def __init__(self):
        self.calls = []

    def run_llm_task(self, config, graph, node_id, prompt_template, variables, **kwargs):
        self.calls.append((node_id, prompt_template, variables))
        graph.update(
            node_id,
            response="FAKE RESPONSE",
            prompt_template=prompt_template,
            status="COMPLETED"
        )
        return "FAKE RESPONSE"

@pytest.fixture(autouse=True)
def patch_template(monkeypatch):
    # Prevent Jinja template loading
    monkeypatch.setattr(template_utils, "render_template", lambda path, vars: "FAKE PROMPT")

@pytest.fixture
def memory_graph_with_nodes(tmp_path):
    graph_path = tmp_path / "test_memory_graph.json"

    # Minimal in-memory graph with parent → child structure
    graph = MemoryGraph(storage_path=graph_path)
    parent_id = graph.new("task_root", tags=["test"], mode="TEST")
    graph.update(parent_id, prompt_template="prompt_1.j2", variables={"x": 1})

    child_id = graph.new("task_child", parent_id=parent_id, tags=["test"], mode="TEST")
    graph.update(child_id, prompt_template="prompt_2.j2", variables={"y": 2})

    return graph, parent_id

def test_replay_subtree_basic(monkeypatch, memory_graph_with_nodes):
    graph, root_id = memory_graph_with_nodes

    dummy = DummyLLMRunner()
    # Patch where run_llm_task is used, not where defined
    monkeypatch.setattr("cybermule.executors.llm_replay.run_llm_task", dummy.run_llm_task)

    config = {}
    prompt_map = {"prompt_2.j2": "prompt_2_v2.j2"}
    replayed = replay_subtree(root_id, graph, config, prompt_map)

    assert len(replayed) == 2

    used_prompts = [call[1] for call in dummy.calls]
    assert "prompt_1.j2" in used_prompts
    assert "prompt_2_v2.j2" in used_prompts

    for new_id in replayed.values():
        node = graph.get(new_id)
        assert node["response"] == "FAKE RESPONSE"
        assert node["status"] == "COMPLETED"
