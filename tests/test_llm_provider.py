from pathlib import Path
import sys
import types
from unittest.mock import MagicMock, patch
from cybermule.providers.llm_provider import LLMResult, MockLLMProvider


def test_build_messages_basic():
    llm = MockLLMProvider()

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
    assert messages[-1]["content"][0]["text"] == prompt
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


def test_generate_and_cache_with_mock(tmp_path: Path):
    cache_path = tmp_path / "mock_cache.json"
    llm = MockLLMProvider(cache_path=str(cache_path))

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


def test_claude_direct_provider_mocked(tmp_path):
    # Step 1: Inject a fake 'anthropic' module with mock client
    fake_module = types.ModuleType("anthropic")
    mock_client_class = MagicMock()
    mock_client_instance = mock_client_class.return_value
    mock_client_instance.messages.create.return_value.content = [
        MagicMock(text="[MOCKED CLAUDE]")
    ]
    fake_module.Anthropic = mock_client_class
    sys.modules["anthropic"] = fake_module

    # Patch real import target BEFORE class instantiation
    with patch("anthropic.Anthropic", new=MagicMock()) as mock_class:
        mock_instance = mock_class.return_value
        mock_instance.messages.create.return_value.content = [
            MagicMock(text="[MOCKED CLAUDE]")
        ]

        from cybermule.providers.llm_provider import ClaudeDirectProvider

        provider = ClaudeDirectProvider(
            api_key="fake",
            model_id="claude-3-sonnet",
            cache_path=str(tmp_path / "cache.json"),
        )

        prompt = "Summarize the article."
        history = (
            {"role": "user", "content": [{"type": "text", "text": "Write a haiku"}]},
            {
                "role": "assistant",
                "content": [{"type": "text", "text": "Gentle wind whispers"}],
            },
        )

        with patch.object(
            ClaudeDirectProvider,
            "_call_api",
            return_value=LLMResult(
                text="[MOCKED CLAUDE]", input_tokens=0, output_tokens=0
            ),
        ) as mock_call:
            response = provider.generate(prompt, history=history)

            mock_call.assert_called_once()
            assert response == "[MOCKED CLAUDE]"

        # Second call should use cache
        with patch.object(ClaudeDirectProvider, "_call_api") as mock_call_2:
            cached = provider.generate(prompt, history=history)
            mock_call_2.assert_not_called()
            assert cached == response


def test_ollama_provider_mocked(tmp_path):
    # Create a fake module with a mocked OllamaLLM class
    fake_module = types.ModuleType("langchain_ollama")
    fake_module.OllamaLLM = MagicMock()
    sys.modules["langchain_ollama"] = fake_module

    # Patch the real source module BEFORE instantiating
    with patch("langchain_ollama.OllamaLLM", new=MagicMock()) as mock_class:
        mock_instance = mock_class.return_value
        mock_instance.invoke.return_value = "[MOCKED OLLAMA]"

        from cybermule.providers.llm_provider import (
            OllamaProvider,
        )  # delay import after patch

        provider = OllamaProvider(
            model_id="mistral",
            base_url="http://localhost:11434",
            cache_path=str(tmp_path / "cache.json"),
        )

        prompt = "Who wrote 'Dune'?"
        history = (
            {
                "role": "user",
                "content": [{"type": "text", "text": "Tell me about sci-fi books"}],
            },
            {"role": "assistant", "content": [{"type": "text", "text": "Sure!"}]},
        )

        with patch.object(
            OllamaProvider,
            "_call_api",
            return_value=LLMResult(
                text="[MOCKED OLLAMA]", input_tokens=0, output_tokens=0
            ),
        ) as mock_call:
            result = provider.generate(prompt, history=history)

            mock_call.assert_called_once()
            assert "[MOCKED OLLAMA]" in result
