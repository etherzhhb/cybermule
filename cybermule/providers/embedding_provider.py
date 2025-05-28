class EmbeddingProvider:
    def embed(self, text: str) -> list[float]:
        raise NotImplementedError

class SentenceTransformerProvider(EmbeddingProvider):
    pass
