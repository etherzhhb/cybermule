import hashlib
import json
import time
from pathlib import Path
from typing import NamedTuple, Optional, Dict, Any, List, Sequence

import typer
from litellm import completion, token_counter

# -------------------------------
# Named result for consistent returns
# -------------------------------
class LLMResult(NamedTuple):
    text: str
    input_tokens: int = 0
    output_tokens: int = 0


# === Self-contained LLM Provider === #
class LLMProvider:
    def __init__(
        self,
        model: str,
        temperature: float = 0.3,
        max_tokens: int = 8192,
        system_prompt: str = '',
        api_key: Optional[str] = None,
        mock_response: Optional[str] = None,
        cache_path: Optional[str] = ".llm_cache.json",
        show_token_summary: bool = True,
        debug_prompt: bool = False
    ):
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self.mock_response = mock_response

        self.cache_path = Path(cache_path).expanduser() if cache_path else None
        self.cache = self._load_cache()
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_calls = 0
        self.show_token_summary = show_token_summary
        self.debug_prompt = debug_prompt

    def _hash_prompt(self, prompt: str, respond_prefix: str, history: Sequence[Dict[str, Any]]) -> str:
        key_material = json.dumps({
            "prompt": prompt,
            "respond_prefix": respond_prefix,
            "history": history,
        }, sort_keys=True)
        return hashlib.sha256(key_material.encode("utf-8")).hexdigest()

    def _load_cache(self) -> Dict[str, str]:
        if self.cache_path is None:
            return {}
        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def _save_cache(self):
        if self.cache_path is None:
            return
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, indent=2)

    def _build_messages(self, prompt: str, respond_prefix: str = '', history: Sequence[Dict[str, Any]] = (),
                        system_prompt: Optional[str] = None) -> List[Dict[str, Any]]:
        messages = list(history)
        final_system_prompt = system_prompt or self.system_prompt
        if final_system_prompt:
            messages = [{"role": "system", "content": final_system_prompt}] + messages
        messages.append({"role": "user", "content": prompt})
        if respond_prefix:
            messages.append({"role": "assistant", "content": respond_prefix})
        return messages

    def generate(self, prompt: str, respond_prefix: str = '', history: Sequence[Dict[str, Any]] = ()) -> str:
        key = self._hash_prompt(prompt, respond_prefix, history)
        if key in self.cache:
            return self.cache[key]

        if self.debug_prompt:
            typer.echo("\n--- Prompt ---\n" + prompt + "\n--- End Prompt ---\n")

        messages = self._build_messages(prompt, respond_prefix, history)
        result = self._call_api(messages)

        self._track_token_usage(result.input_tokens, result.output_tokens)
        self.cache[key] = result.text
        self._save_cache()
        return result.text

    def _call_api(self, messages: List[Dict[str, Any]]) -> LLMResult:
        if self.mock_response is not None:
            return LLMResult(text=self.mock_response, input_tokens=0, output_tokens=0)

        # Count prompt tokens before streaming
        input_tokens = token_counter(model=self.model, messages=messages)

        # Initialize variables for output
        content = ""
        output_tokens = 0
        usage_tokens = None  # To store usage info from the final chunk

        # Initiate streaming with usage tracking
        response = completion(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            api_key=self.api_key,
            stream=True,
            stream_options={"include_usage": True}  # Enables usage info in the final chunk
        )

        for chunk in response:
            # Check if the chunk contains content
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                chunk_content = chunk.choices[0].delta.content
                content += chunk_content
                typer.echo(chunk_content if self.debug_prompt else '.', nl=False)
                output_tokens += 1  # Increment output token count

            # Check if the chunk contains usage information
            if hasattr(chunk, 'usage') and chunk.usage:
                usage_tokens = chunk.usage  # Store usage info from the final chunk

        typer.echo()  # Add newline after streaming

        # If usage info is available, update token counts
        if usage_tokens:
            input_tokens = usage_tokens.get("prompt_tokens", input_tokens)
            output_tokens = usage_tokens.get("completion_tokens", output_tokens)

        return LLMResult(
            text=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )

    def _track_token_usage(self, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_calls += 1
        if self.show_token_summary:
            typer.echo(f"💸 Token Summary: {self.token_summary}")

    @property
    def token_summary(self) -> dict:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_calls": self.total_calls,
        }


def get_llm_provider(config, disable_caching=False) -> LLMProvider:
    llm_cfg = config.get("litellm", {})
    provider_kwargs = dict(llm_cfg)
    if disable_caching:
        provider_kwargs["cache_path"] = None
    return LLMProvider(**provider_kwargs)
