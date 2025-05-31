import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple


# === Unified Interface === #
class LLMProvider:
    def __init__(self, cache_path: str = ".llm_cache.json"):
        self.cache_path = Path(cache_path).expanduser()
        self.cache = self._load_cache()

    def _hash_prompt(
        self,
        prompt: str,
        respond_prefix: str,
        history: Tuple[Dict[str, Any], ...]
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
        history: Tuple[Dict[str, Any], ...] = (),
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
        history: Tuple[Dict[str, Any], ...] = ()
    ) -> str:
        key = self._hash_prompt(prompt, respond_prefix, history)
        if key in self.cache:
            return self.cache[key]

        messages = self._build_messages(prompt, respond_prefix, history)
        response = self._call_api(messages)

        self.cache[key] = response
        self._save_cache()
        return response

    def _call_api(self, messages: List[Dict[str, Any]]) -> str:
        raise NotImplementedError


# === Claude Base Implementation === #
class ClaudeBaseProvider(LLMProvider):
    def __init__(
        self,
        model_id: str,
        temperature: float = 0.7,
        max_tokens: int = 20000,
        system_prompt: str = '',
        **kwargs
    ):
        super().__init__(**kwargs)
        self.model_id = model_id
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt

    def _call_api(self, messages: List[Dict[str, Any]]) -> str:
        raise NotImplementedError


# === Claude Bedrock Implementation === #
class ClaudeBedrockProvider(ClaudeBaseProvider):
    def __init__(self, model_id: str, region: str, **kwargs):
        super().__init__(model_id=model_id, **kwargs)
        import boto3
        self.client = boto3.client("bedrock-runtime", region_name=region)

    def _call_api(self, messages: List[Dict[str, Any]]) -> str:
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        response = self.client.invoke_model(
            modelId=self.model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body)
        )

        result = json.loads(response['body'].read())
        return result["content"][0]["text"]


# === Claude Direct API Implementation === #
class ClaudeDirectProvider(ClaudeBaseProvider):
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)

    def _call_api(self, messages: List[Dict[str, Any]]) -> str:
        message = self.client.messages.create(
            model=self.model_id,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=messages
        )
        return message.content[0].text


# === Ollama Implementation === #
class OllamaProvider(LLMProvider):
    def __init__(self, model_id: str, base_url=None, **kwargs):
        super().__init__(**kwargs)
        from langchain_ollama import OllamaLLM
        self.llm = OllamaLLM(model=model_id, base_url=base_url)

    def _call_api(self, messages: List[Dict[str, Any]]) -> str:
        flat_prompt = self._flatten_messages(messages)
        return self.llm.invoke(flat_prompt)

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

    def _call_api(self, messages: List[Dict[str, Any]]) -> str:
        parts = []
        for m in messages:
            role = m.get("role", "user").capitalize()
            content = "".join(chunk["text"] for chunk in m["content"] if chunk["type"] == "text")
            parts.append(f"{role}: {content}")
        return f"[MOCKED] Response to: {' | '.join(parts)}"


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
