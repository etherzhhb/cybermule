# File: tests/test_prompt_eval.py

import pytest
import json
from cybermule.memory.memory_graph import MemoryGraph
from cybermule.executors.prompt_eval import evaluate_prompt_variants

@pytest.fixture
def fake_prompt_variants(tmp_path):
    # Write two different prompt templates
    t1 = tmp_path / "t1.j2"
    t2 = tmp_path / "t2.j2"
    eval_template = tmp_path / "evaluate_prompt_variants.j2"

    t1.write_text("Prompt V1 for {{ name }}")
    t2.write_text("Prompt V2 for {{ name }}")
    eval_template.write_text("""
    Evaluate based on goal: {{ goal }}

    {% for variant in variants %}
    === Variant {{ loop.index }} ===
    {{ variant.full_prompt }}
    {{ variant.response }}
    {% endfor %}
    """)

    return {"t1": t1, "t2": t2, "eval": eval_template}


@pytest.fixture
def patch_prompt_utils(monkeypatch, fake_prompt_variants):
    monkeypatch.setattr(
        "cybermule.executors.prompt_eval.get_prompt_path",
        lambda config, name: fake_prompt_variants.get(name.split(".")[0])  # t1 → fake_prompt_variants["t1"]
    )


@pytest.fixture
def fake_llm_eval(monkeypatch):
    class DummyLLM:
        def generate(self, prompt: str, respond_prefix: str = '', history = ()):
            result = json.dumps({
                "preferred": "t2.j2",
                "scores": {
                    "t1.j2": 3,
                    "t2.j2": 9
                },
                "justification": "t2 is clearer."
            })
            return f"```json\n{result}\n```"

    monkeypatch.setattr("cybermule.executors.prompt_eval.get_llm_provider", lambda config: DummyLLM())


def test_evaluate_prompt_variants_basic(tmp_path, patch_prompt_utils, fake_llm_eval, fake_prompt_variants):
    graph = MemoryGraph(storage_path=tmp_path / "variants.json")

    n1 = graph.new("v1")
    graph.update(n1, prompt_template="t1.j2", variables={"name": "Alice"}, response="Response from V1")

    n2 = graph.new("v2")
    graph.update(n2, prompt_template="t2.j2", variables={"name": "Alice"}, response="Response from V2")

    result = evaluate_prompt_variants(
        node_ids=[n1, n2],
        graph=graph,
        config={},
        goal="clarity",
        prompt_template="eval"
    )

    assert result["preferred"] == "t2.j2"
    assert "scores" in result
    assert result["scores"]["t1.j2"] == 3
    assert result["scores"]["t2.j2"] == 9
