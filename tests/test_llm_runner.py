import pytest
from pathlib import Path
from cybermule.memory.memory_graph import MemoryGraph
from cybermule.executors.llm_runner import run_llm_and_store, run_llm_task


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
        "cybermule.executors.llm_runner.get_prompt_path",
        lambda config, name: Path(fake_prompt_file)
    )

@pytest.fixture
def fake_llm(monkeypatch):
    """Patch get_llm_provider to return a dummy LLM"""
    class DummyLLM:
        def generate(self, prompt, history=None, respond_prefix=None):
            return f"Response to: {prompt}"

    monkeypatch.setattr(
        "cybermule.executors.llm_runner.get_llm_provider",
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

def test_run_llm_task_with_history(
    patch_prompt_path, patch_version_info, monkeypatch
):
    mock_history = [{"role": "assistant", "content": "Earlier step"}]

    # Patch extract_chat_history to return mock
    monkeypatch.setattr(
        "cybermule.executors.llm_runner.extract_chat_history",
        lambda parent_id, memory: mock_history
    )

    # Use an LLM that returns history content in response
    class HistoryEchoLLM:
        def generate(self, prompt, history=None, respond_prefix=None):
            history_snippet = history[0]["content"] if history else "NO_HISTORY"
            return f"Prompt: {prompt} | History: {history_snippet}"

    monkeypatch.setattr(
        "cybermule.executors.llm_runner.get_llm_provider",
        lambda config: HistoryEchoLLM()
    )

    graph = MemoryGraph()
    parent_id = graph.new("Parent node", tags=["trace"])
    graph.update(parent_id, prompt="prompt", response="Earlier step")

    node_id = graph.new("Child node", tags=["test"], parent_id=parent_id)

    response = run_llm_task(
        config={},
        graph=graph,
        node_id=node_id,
        prompt_template="test_prompt.j2",
        variables={"name": "Cybermule"},
    )

    # ✅ Check that history made it into LLM response
    assert "Earlier step" in response


def test_run_llm_task_with_respond_prefix(
    patch_prompt_path, patch_version_info, monkeypatch
):
    # Capture passed respond_prefix
    captured = {}

    class DummyLLM:
        def generate(self, prompt, history=None, respond_prefix=None):
            captured["prefix"] = respond_prefix
            return "Some response"

    monkeypatch.setattr("cybermule.executors.llm_runner.get_llm_provider", lambda cfg: DummyLLM())

    graph = MemoryGraph()
    node_id = graph.new("Test prefix", tags=["prefix"])

    run_llm_task(
        config={},
        graph=graph,
        node_id=node_id,
        prompt_template="test_prompt.j2",
        variables={"name": "Test"},
        respond_prefix="OUTPUT:\n"
    )

    assert captured["prefix"] == "OUTPUT:\n"

def test_run_llm_task_chain_lineage(
    patch_prompt_path, fake_llm, patch_version_info
):
    graph = MemoryGraph()
    root_id = graph.new("Root reasoning step", tags=["chain"])
    next_id = graph.new("Step 2", tags=["chain"], parent_id=root_id,)

    # Perform task as child of root
    response = run_llm_task(
        config={},
        graph=graph,
        node_id=next_id,
        prompt_template="test_prompt.j2",
        variables={"name": "Followup"},
        status="CHAINED",
        extra={"step": 2}
    )

    node = graph.get(next_id)
    assert node["status"] == "CHAINED"
    assert node["step"] == 2
    assert node["prompt"].startswith("Hello, Followup")
    assert "Response to:" in node["response"]

def test_run_llm_task_defaults(
    patch_prompt_path, fake_llm, patch_version_info
):
    graph = MemoryGraph()
    node_id = graph.new("No extras")

    response = run_llm_task(
        config={},
        graph=graph,
        node_id=node_id,
        prompt_template="test_prompt.j2",
        variables={"name": "Bare"},
    )

    node = graph.get(node_id)

    assert node["prompt"] == "Hello, Bare!"
    assert node["response"] == response
    assert node["status"] == "COMPLETED"
    assert "custom_meta" not in node
    assert not node['tags']

def test_run_llm_task_render_error(monkeypatch, tmp_path, patch_version_info):
    bad_prompt = tmp_path / "bad_prompt.j2"
    bad_prompt.write_text("{{ undefined_var | upper }} {{")  # malformed

    monkeypatch.setattr(
        "cybermule.executors.llm_runner.get_prompt_path",
        lambda cfg, name: bad_prompt
    )

    class DummyLLM:
        def generate(self, prompt, history=None, respond_prefix=None):
            return "should not run"

    monkeypatch.setattr(
        "cybermule.executors.llm_runner.get_llm_provider",
        lambda cfg: DummyLLM()
    )

    graph = MemoryGraph()
    node_id = graph.new("Broken")

    with pytest.raises(Exception):
        run_llm_task(
            config={},
            graph=graph,
            node_id=node_id,
            prompt_template="bad_prompt.j2",
            variables={"irrelevant": "value"}
        )

def test_run_llm_and_store_basic(
    patch_prompt_path, fake_llm, patch_version_info
):
    graph = MemoryGraph()
    node_id = graph.new("Test store", tags=["unit"])

    response, metadata = run_llm_and_store(
        config={},
        graph=graph,
        node_id=node_id,
        prompt_template="test_prompt.j2",
        variables={"name": "Cybermule"},
        status="STORE_TEST",
        postprocess=lambda r: {"parsed_result": r.upper()}
    )

    node = graph.get(node_id)

    # ✅ Check response passthrough
    assert response == "Response to: Hello, Cybermule!"

    # ✅ Check postprocess result is stored
    assert metadata == {"parsed_result": "RESPONSE TO: HELLO, CYBERMULE!"}
    assert node["parsed_result"] == metadata["parsed_result"]
    assert node["status"] == "STORE_TEST"
