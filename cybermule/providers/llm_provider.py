import hashlib
import json
from pathlib import Path
import time
from typing import NamedTuple, Optional, Dict, Any, List, Sequence, Tuple

import typer

# -------------------------------
# Named result for consistent returns
# -------------------------------
class LLMResult(NamedTuple):
    text: str
    input_tokens: int = 0
    output_tokens: int = 0

# === Unified Interface === #
class LLMProvider:
    def __init__(self, cache_path: str = ".llm_cache.json", show_token_summary=True, 
                 debug_prompt=False):
        self.cache_path = Path(cache_path).expanduser()
        self.cache = self._load_cache()
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_calls = 0
        self.show_token_summary = show_token_summary
        self.debug_prompt = debug_prompt

    def _hash_prompt(
        self,
        prompt: str,
        respond_prefix: str,
        history: Sequence[Dict[str, Any]]
    ) -> str:
        key_material = json.dumps({
            "prompt": prompt,
            "respond_prefix": respond_prefix,
            "history": history,
        }, sort_keys=True)
        return hashlib.sha256(key_material.encode("utf-8")).hexdigest()

    def _load_cache(self) -> Dict[str, str]:
        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def _save_cache(self):
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, indent=2)

    def _build_messages(
        self,
        prompt: str,
        respond_prefix: str = '',
        history: Sequence[Dict[str, Any]] = (),
        system_prompt: str = ''
    ) -> List[Dict[str, Any]]:
        messages = list(history)

        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages

        messages.append({
            "role": "user",
            "content": [{"type": "text", "text": prompt}]
        })

        if respond_prefix:
            messages.append({
                "role": "assistant",
                "content": [{"type": "text", "text": respond_prefix}]
            })

        return messages

    def generate(
        self,
        prompt: str,
        respond_prefix: str = '',
        history: Sequence[Dict[str, Any]] = ()
    ) -> str:
        key = self._hash_prompt(prompt, respond_prefix, history)
        if key in self.cache:
            return self.cache[key]

        if self.debug_prompt:
            typer.echo("\n--- Prompt ---\n" + prompt + "\n--- End Prompt ---\n")

        messages = self._build_messages(prompt, respond_prefix=respond_prefix,
                                        history=history)
        result = self._call_api(messages, respond_prefix=respond_prefix)

        self._track_token_usage(result.input_tokens, result.output_tokens)
        self.cache[key] = result.text

        self._save_cache()
        return result.text

    def _call_api(self, messages: List[Dict[str, Any]], respond_prefix) -> LLMResult:
        raise NotImplementedError

    def _track_token_usage(self, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_calls += 1
        
        # Print token summary with $ emoji if enabled
        if self.show_token_summary:
            typer.echo(f"💸 Token Summary: {self.token_summary}")

    @property
    def token_summary(self) -> dict:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_calls": self.total_calls,
        }


# === Claude Base Implementation === #
class ClaudeBaseProvider(LLMProvider):
    def __init__(
        self,
        model_id: str,
        temperature: float = 0.3,
        max_tokens: int = 20000,
        system_prompt: str = '',
        **kwargs
    ):
        super().__init__(**kwargs)
        self.model_id = model_id
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt

    def _call_api(self, messages: List[Dict[str, Any]], respond_prefix) -> LLMResult:
        raise NotImplementedError


# === Claude Bedrock Implementation === #
class ClaudeBedrockProvider(ClaudeBaseProvider):
    def __init__(self, model_id: str, region: str, **kwargs):
        super().__init__(model_id=model_id, **kwargs)
        import boto3
        self.client = boto3.client("bedrock-runtime", region_name=region)

    def _call_api(self, messages: List[Dict[str, Any]], respond_prefix) -> LLMResult:
        from botocore.exceptions import ClientError

        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        max_retries, delay = 5, 2 # initial delay in seconds
        for attempt in range(1, max_retries + 1):
            try:
                response = self.client.invoke_model_with_response_stream(
                    modelId=self.model_id,
                    body=json.dumps(payload),
                    contentType="application/json",
                    accept="application/json",
                )

                full_text = str(respond_prefix)
                input_tokens = output_tokens = 0

                for event in response.get("body", []):
                    chunk = event.get("chunk")
                    if not chunk:
                        continue
                    block = json.loads(chunk["bytes"].decode())

                    if block.get("type") == "content_block_delta":
                        delta = block.get("delta", {}).get("text", "")
                        typer.echo(delta, nl=False)
                        full_text += delta
                    elif block.get("type") == "message_start":
                      usage = block.get("message", {}).get("usage", {})
                      input_tokens = usage.get("input_tokens", 0)
                    elif block.get("type") == "message_delta":
                      usage = block.get("usage", {})
                      output_tokens = usage.get("output_tokens", 0)

                typer.echo()  # newline after stream
                return LLMResult(text=full_text, input_tokens=input_tokens, output_tokens=output_tokens)

            except ClientError as e:
                typer.secho(
                    f"⚠️ Bedrock API error on attempt {attempt}/{max_retries}: {str(e)}",
                    fg=typer.colors.YELLOW,
                )
                if attempt == max_retries:
                    typer.secho("🚨 Claude API retries exhausted.", fg=typer.colors.RED, bold=True)
                    raise RuntimeError("Claude Bedrock API failed repeatedly") from e
                time.sleep(delay)
                delay *= 2

# === Claude Direct API Implementation === #
class ClaudeDirectProvider(ClaudeBaseProvider):
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)

    def _call_api(self, messages: List[Dict[str, Any]], respond_prefix) -> LLMResult:
        from anthropic._exceptions import OverloadedError

        max_retries, delay = 5, 2 # initial delay in seconds
        
        for attempt in range(1, max_retries + 1):
            try:
                with self.client.messages.stream(
                    model=self.model_id,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    messages=messages,
                ) as stream:
                    full_text = str(respond_prefix)
                    for text in stream.text_stream:
                        typer.echo(text if self.debug_prompt else '.', nl=False)
                        full_text += text
                    typer.echo()  # Newline after streaming
                    final_message = stream.get_final_message()
                    return LLMResult(
                        text=full_text,
                        input_tokens=final_message.usage.input_tokens,
                        output_tokens=final_message.usage.output_tokens,
                    )
            except OverloadedError as e:
                if attempt == max_retries:
                    typer.secho("🚨 Claude API overloaded (529), retries exhausted.", fg=typer.colors.RED, bold=True)
                    raise RuntimeError("Claude API overloaded (529), retries exhausted.") from e
                typer.secho(f"⚠️ Claude API overloaded (529). Retrying in {delay} seconds... (Attempt {attempt}/{max_retries})", fg=typer.colors.YELLOW)
                time.sleep(delay)
                delay *= 2  # exponential backoff

# === Ollama Implementation === #
class OllamaProvider(LLMProvider):
    def __init__(self, model_id: str, base_url=None, **kwargs):
        super().__init__(**kwargs)
        from langchain_ollama import OllamaLLM
        self.llm = OllamaLLM(model=model_id, base_url=base_url)

    def _call_api(self, messages: List[Dict[str, Any]], respond_prefix) -> LLMResult:
        flat_prompt = self._flatten_messages(messages)
        output = self.llm.invoke(flat_prompt)

        if self.debug_prompt:
            typer.echo("\n--- Respond ---\n" + output + "\n--- End Respond ---\n")            

        return LLMResult(
            text=output,
            input_tokens=len(flat_prompt.split()),
            output_tokens=len(output.split())
        )

    def _flatten_messages(self, messages: List[Dict[str, Any]]) -> str:
        parts = []
        for m in messages:
            role = m.get("role", "user").capitalize()
            content = "".join(chunk["text"] for chunk in m["content"] if chunk["type"] == "text")
            parts.append(f"{role}: {content}")
        return "\n".join(parts)


# === Mock Implementation for Testing === #
class MockLLMProvider(LLMProvider):
    def __init__(self, model_id=None, **kwargs):
        super().__init__(**kwargs)
        self.model_id = model_id or "mock"

    def _call_api(self, messages: List[Dict[str, Any]], respond_prefix) -> LLMResult:
        parts = []
        for m in messages:
            role = m.get("role", "user").capitalize()
            content = "".join(chunk["text"] for chunk in m["content"] if chunk["type"] == "text")
            parts.append(f"{role}: {content}")
        mock_response = f"[MOCKED] Response to: {' | '.join(parts)}"

        if self.debug_prompt:
            typer.echo("\n--- Respond ---\n" + mock_response + "\n--- End Respond ---\n")     

        return LLMResult(
            text=mock_response,
            input_tokens=len(' '.join(parts).split()),
            output_tokens=len(mock_response.split())
        )


# === Optional Factory === #
LLM_REGISTRY = {
    "aws": ClaudeBedrockProvider,
    "anthropic": ClaudeDirectProvider,
    "ollama": OllamaProvider,
    "mock": MockLLMProvider,
    # Future: "openai": OpenAIProvider,
}

def get_llm_provider(config) -> LLMProvider:
    llm_cfg = config.get("llm", {})
    name = llm_cfg.get("provider", None)
    if not name:
        raise ValueError("'provider' must be specified in llm config")

    if name not in LLM_REGISTRY:
        raise ValueError(f"Unknown LLM provider: {name}")

    provider_kwargs = {k: v for k, v in llm_cfg.items() if k != "provider"}
    return LLM_REGISTRY[name](**provider_kwargs)
