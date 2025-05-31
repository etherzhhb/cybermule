import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

# === Unified Interface === #
class LLMProvider:
    def __init__(self, cache_path: str = ".llm_cache.json"):
        self.cache_path = Path(cache_path).expanduser()
        self.cache = self._load_cache()

    def _hash_prompt(self, prompt: str, respond_prefix: str, history: tuple[str, ...]) -> str:
        key_material = json.dumps({
            "prompt": prompt,
            "respond_prefix": respond_prefix,
            "history": history,
        }, sort_keys=True)
        return hashlib.sha256(key_material.encode('utf-8')).hexdigest()

    def _load_cache(self):
        try:
            with open(self.cache_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def _save_cache(self):
        with open(self.cache_path, 'w') as f:
            json.dump(self.cache, f, indent=2)

    def generate(self, prompt: str, respond_prefix: str = '', history: tuple[str, ...] = ()) -> str:
        key = self._hash_prompt(prompt, respond_prefix, history)
        if key in self.cache:
            return self.cache[key]

        response = self.generate_impl(prompt, respond_prefix=respond_prefix, history=history)
        self.cache[key] = response
        self._save_cache()
        return response

    def generate_impl(self, prompt: str, respond_prefix: str = '', history: tuple[str, ...] = ()) -> str:
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

    def _format_messages(self, prompt: str, history: tuple[str, ...]) -> List[Dict[str, Any]]:
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})

        roles = ["user", "assistant"]
        for i, msg in enumerate(history):
            messages.append({"role": roles[i % 2], "content": [{"type": "text", "text": msg}]})

        messages.append({"role": "user", "content": [{"type": "text", "text": prompt}]})
        return messages

    def generate_impl(self, prompt: str, respond_prefix: str = '', history: tuple[str, ...] = ()) -> str:
        messages = self._format_messages(prompt, history)
        if respond_prefix:
            messages.append({"role": "assistant", "content": [{"type": "text", "text": respond_prefix}]})
        return self._call_api(messages)

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


# === OllamaLLM Implementation === #
class OllamaProvider(LLMProvider):
    def __init__(self, model_id: str, base_url=None, **kwargs):
        super().__init__(**kwargs)
        from langchain_ollama import OllamaLLM
        self.llm = OllamaLLM(model=model_id, base_url=base_url)

    def generate_impl(self, prompt: str, respond_prefix: str = '', history: tuple[str, ...] = ()) -> str:
        return self.llm.invoke(prompt)


# === Mock Implementation for Testing === #
class MockLLMProvider(LLMProvider):
    def __init__(self, model_id=None, **kwargs):
        super().__init__(**kwargs)
        self.model_id = model_id or "mock"

    def generate(self, prompt: str, respond_prefix: str = '', history: tuple[str, ...] = ()) -> str:
        parts = list(history) + [prompt]
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
