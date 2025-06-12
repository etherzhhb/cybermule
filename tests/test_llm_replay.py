# File: tests/test_llm_replay.py

import pytest
from cybermule.executors.llm_replay import replay_subtree
from cybermule.memory.memory_graph import MemoryGraph

# Creates a temporary .j2 prompt file with a template variable
@pytest.fixture
def fake_prompt_file(tmp_path):
    file = tmp_path / "replay_prompt.j2"
    file.write_text("Sim {{ name }}!")
    return file

# Patches get_prompt_path to always return the fake template
@pytest.fixture
def patch_prompt_path(monkeypatch, fake_prompt_file):
    monkeypatch.setattr(
        "cybermule.executors.llm_runner.get_prompt_path",
        lambda config, name: fake_prompt_file
    )

# Patches LLM provider to return a predictable fake result
@pytest.fixture
def fake_llm(monkeypatch):
    class FakeLLM:
        def generate(self, prompt, history=None, respond_prefix=None):
            return f"[FAKE] {prompt}"
    monkeypatch.setattr(
        "cybermule.executors.llm_runner.get_llm_provider",
        lambda config: FakeLLM()
    )

# ✅ Basic replay with prompt substitution
def test_replay_subtree_basic(tmp_path, patch_prompt_path, fake_llm):
    graph = MemoryGraph(storage_path=tmp_path / "basic.json")
    root = graph.new("task_root")
    graph.update(root, prompt_template="template_a.j2", variables={"name": "Alice"})
    child = graph.new("task_child", parent_id=root)
    graph.update(child, prompt_template="template_b.j2", variables={"name": "Bob"})

    replayed = replay_subtree(root, graph, {}, {"template_b.j2": "template_b_alt.j2"})
    assert len(replayed) == 2

    replayed_child = graph.get(replayed[child])
    assert replayed_child["prompt_template"] == "template_b_alt.j2"
    assert replayed_child["response"].startswith("[FAKE]")

# ✅ Check replay_of and prompt_variant_of fields
def test_lineage_tracking(tmp_path, patch_prompt_path, fake_llm):
    graph = MemoryGraph(storage_path=tmp_path / "lineage.json")
    orig = graph.new("task", tags=["unit"])
    graph.update(orig, prompt_template="t1.j2", variables={"name": "X"})

    replayed = replay_subtree(orig, graph, {}, {"t1.j2": "t2.j2"})
    new_node = graph.get(replayed[orig])
    assert new_node["replay_of"] == orig
    assert new_node["prompt_variant_of"] == "t1.j2"
    assert new_node["prompt_template"] == "t2.j2"

# ✅ Multilevel DAG: A → B → C
def test_multilevel_dag(tmp_path, patch_prompt_path, fake_llm):
    graph = MemoryGraph(storage_path=tmp_path / "dag.json")
    a = graph.new("task_a")
    graph.update(a, prompt_template="a.j2", variables={"name": "A"})
    b = graph.new("task_b", parent_id=a)
    graph.update(b, prompt_template="b.j2", variables={"name": "B"})
    c = graph.new("task_c", parent_id=b)
    graph.update(c, prompt_template="c.j2", variables={"name": "C"})

    replayed = replay_subtree(a, graph, {}, {"b.j2": "b_alt.j2"})

    assert graph.get(replayed[b])["prompt_template"] == "b_alt.j2"
    assert graph.get(replayed[c])["parent"] == replayed[b]

# ✅ Sibling branches: A → B1, B2
def test_parallel_branches(tmp_path, patch_prompt_path, fake_llm):
    graph = MemoryGraph(storage_path=tmp_path / "branches.json")
    root = graph.new("task_root")
    graph.update(root, prompt_template="root.j2", variables={})
    b1 = graph.new("task_b1", parent_id=root)
    graph.update(b1, prompt_template="b1.j2", variables={})
    b2 = graph.new("task_b2", parent_id=root)
    graph.update(b2, prompt_template="b2.j2", variables={})

    replayed = replay_subtree(root, graph, {}, {"b2.j2": "b2_alt.j2"})

    node = graph.get(replayed[b2])
    assert node["prompt_template"] == "b2_alt.j2"
    assert node["prompt_variant_of"] == "b2.j2"
    assert node["parent"] == replayed[root]

# ✅ Identity replay — no substitution
def test_identity_replay(tmp_path, patch_prompt_path, fake_llm):
    graph = MemoryGraph(storage_path=tmp_path / "identity.json")
    root = graph.new("task_identity")
    graph.update(root, prompt_template="noop.j2", variables={"name": "Z"})

    replayed = replay_subtree(root, graph, {}, {})  # no substitution
    node = graph.get(replayed[root])
    assert node["prompt_template"] == "noop.j2"
    assert node.get("prompt_variant_of") is None
