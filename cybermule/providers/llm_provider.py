from abc import ABC, abstractmethod
import json
from pathlib import Path
import yaml

# === Unified Interface === #
class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        pass


# === Claude Implementation === #
class ClaudeBedrockProvider(LLMProvider):
    def __init__(self, model_id, region, temperature=0.7, max_tokens=1024, system_prompt=''):
        import boto3
        self.model_id = model_id
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self.client = boto3.client("bedrock-runtime", region_name=region)

    def generate(self, prompt: str) -> str:
        messages = []

        system_prompt = self.system_prompt
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

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
        return result["content"][0]["text"]  # May vary depending on Claude output format

# === Optional Factory === #
LLM_REGISTRY = {
    "claude": ClaudeBedrockProvider,
    # Future: "openai": OpenAIProvider,
}

def get_llm_provider(config_path: str = "config.yaml") -> LLMProvider:
    with open(Path(config_path), "r") as f:
        config = yaml.safe_load(f)

    llm_cfg = config.get("llm", {})
    name = llm_cfg.pop("provider", None)
    if not name:
        raise ValueError("'provider' must be specified in llm config")

    if name not in LLM_REGISTRY:
        raise ValueError(f"Unknown LLM provider: {name}")

    return LLM_REGISTRY[name](**llm_cfg)
