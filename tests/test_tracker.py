import pytest
from pathlib import Path
from cybermule.memory.memory_graph import MemoryGraph
from cybermule.memory.tracker import run_llm_task


# ─── Fixtures and Mocks ─────────────────────────────────────────────────────────

@pytest.fixture
def fake_prompt_file(tmp_path):
    """Create a temporary Jinja2 prompt file with a variable"""
    prompt_file = tmp_path / "test_prompt.j2"
    prompt_file.write_text("Hello, {{ name }}!")
    return prompt_file

@pytest.fixture
def patch_prompt_path(monkeypatch, fake_prompt_file):
    """Patch get_prompt_path to return the fake prompt"""
    monkeypatch.setattr(
        "cybermule.memory.tracker.get_prompt_path",
        lambda config, name: Path(fake_prompt_file)
    )

@pytest.fixture
def fake_llm(monkeypatch):
    """Patch get_llm_provider to return a dummy LLM"""
    class DummyLLM:
        def generate(self, prompt, history=None, respond_prefix=None):
            return f"Response to: {prompt}"

    monkeypatch.setattr(
        "cybermule.memory.tracker.get_llm_provider",
        lambda config: DummyLLM()
    )

@pytest.fixture
def patch_version_info(monkeypatch):
    """Patch get_version_info to return a dummy git commit"""
    monkeypatch.setattr(
        "cybermule.memory.tracker.get_version_info",
        lambda: {"git_commit": "abc123"}
    )

# ─── Main Test ───────────────────────────────────────────────────────────────────

def test_run_llm_task_basic(
    patch_prompt_path, fake_llm, patch_version_info
):
    graph = MemoryGraph()
    node_id = graph.new("Test node", tags=["unit"])

    response = run_llm_task(
        config={},  # config is ignored due to patch
        graph=graph,
        node_id=node_id,
        prompt_template="test_prompt.j2",
        variables={"name": "Cybermule"},
        status="DONE",
        tags=["test"],
        extra={"custom_meta": "ok"}
    )

    node = graph.get(node_id)

    # ✅ Check LLM output
    assert response == "Response to: Hello, Cybermule!"

    # ✅ Check MemoryGraph updates
    assert node["prompt"] == "Hello, Cybermule!"
    assert node["response"] == response
    assert node["prompt_template"] == "test_prompt.j2"
    assert node["cybermule_commit"] == "abc123"
    assert node["status"] == "DONE"
    assert node["custom_meta"] == "ok"
