import tempfile
from pathlib import Path
from cybermule.providers.llm_provider import LLMProvider, MockLLMProvider


class CountingMockLLMProvider(MockLLMProvider):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.call_count = 0

    def _call_api(self, messages):
        self.call_count += 1
        return super()._call_api(messages)


def test_build_messages_basic():
    llm = LLMProvider()

    prompt = "What is the capital of France?"
    history = (
        {"role": "user", "content": [{"type": "text", "text": "Who is the president of France?"}]},
        {"role": "assistant", "content": [{"type": "text", "text": "Emmanuel Macron"}]},
    )

    messages = llm._build_messages(prompt, history=history)
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"][0]["text"] == prompt
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


def test_generate_and_cache_with_mock(tmp_path: Path):
    cache_path = tmp_path / "mock_cache.json"
    llm = CountingMockLLMProvider(cache_path=str(cache_path))

    prompt = "What is 2 + 2?"
    history = (
        {"role": "user", "content": [{"type": "text", "text": "Say hello."}]},
        {"role": "assistant", "content": [{"type": "text", "text": "Hello!"}]},
    )

    # First call — should trigger _call_api
    response1 = llm.generate(prompt, history=history)
    assert llm.call_count == 1

    # Second call — should come from cache
    response2 = llm.generate(prompt, history=history)
    assert llm.call_count == 1  # Still 1 → no new API call

    assert response1 == response2
    assert cache_path.exists()
