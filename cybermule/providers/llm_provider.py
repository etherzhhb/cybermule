from abc import ABC, abstractmethod
import json

# === Unified Interface === #
class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        pass


# === Claude Implementation === #
class ClaudeBedrockProvider(LLMProvider):
    def __init__(self, model_id="anthropic.claude-3-sonnet-20240229", region="us-east-1"):
        import boto3
        self.model_id = model_id
        self.client = boto3.client("bedrock-runtime", region_name=region)

    def generate(self, prompt: str, **kwargs) -> str:
        system_prompt = kwargs.get("system_prompt")
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 1024)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
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

def get_llm_provider(name: str, **config) -> LLMProvider:
    if name not in LLM_REGISTRY:
        raise ValueError(f"Unknown LLM provider: {name}")
    return LLM_REGISTRY[name](**config)
