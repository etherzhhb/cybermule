from abc import ABC, abstractmethod
from typing import List
from cybermule.tools.config_loader import load_config


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Convert input text to a vector embedding."""
        pass


class MockEmbeddingProvider(EmbeddingProvider):
    def embed(self, text: str) -> List[float]:
        return [0.1] * 768


class SentenceTransformerProvider(EmbeddingProvider):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise ImportError(
                "SentenceTransformer is not installed. "
                "Please install it via 'pip install sentence-transformers'."
            ) from e
        self.model = SentenceTransformer(model_name)

    def embed(self, text: str) -> List[float]:
        return self.model.encode([text])[0].tolist()


def get_embedding_provider() -> EmbeddingProvider:
    config = load_config()

    embedding_cfg = config.get("embedding", {})
    provider = embedding_cfg.get("provider", "mock")

    if provider == "sentence-transformers":
        model = embedding_cfg.get("model", "all-MiniLM-L6-v2")
        return SentenceTransformerProvider(model)
    elif provider == "mock":
        return MockEmbeddingProvider()
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")
