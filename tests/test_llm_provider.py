from pathlib import Path
from cybermule.providers.llm_provider import LLMProvider


def test_build_messages_basic():
    llm = LLMProvider("mock")

    prompt = "What is the capital of France?"
    history = (
        {
            "role": "user",
            "content": [{"type": "text", "text": "Who is the president of France?"}],
        },
        {"role": "assistant", "content": [{"type": "text", "text": "Emmanuel Macron"}]},
    )

    messages = llm._build_messages(prompt, history=history)
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == prompt
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


def test_generate_and_cache_with_mock(tmp_path: Path):
    cache_path = tmp_path / "mock_cache.json"
    llm = LLMProvider("mock", cache_path=str(cache_path), mock_response="aha")

    prompt = "What is 2 + 2?"
    history = (
        {"role": "user", "content": [{"type": "text", "text": "Say hello."}]},
        {"role": "assistant", "content": [{"type": "text", "text": "Hello!"}]},
    )

    # First call — should trigger _call_api
    response1 = llm.generate(prompt, history=history)
    assert llm.total_calls == 1

    # Second call — should come from cache
    response2 = llm.generate(prompt, history=history)
    assert llm.total_calls == 1  # Still 1 → no new API call

    assert response1 == response2
    assert cache_path.exists()
