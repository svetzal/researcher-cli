from typing import Any


class EmbeddingGateway:
    """Provides embedding generation with multiple backend support."""

    def __init__(self, provider: str = "chromadb", model: str | None = None):
        self._provider = provider
        self._model = model
        self._chromadb_ef: Any = None

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        if self._provider == "chromadb":
            return self._embed_with_chromadb(texts)
        elif self._provider == "ollama":
            return self._embed_with_ollama(texts)
        elif self._provider == "openai":
            return self._embed_with_openai(texts)
        else:
            raise ValueError(f"Unknown embedding provider: {self._provider}")

    def embed_query(self, query: str) -> list[float]:
        """Generate an embedding for a single query string."""
        return self.embed_texts([query])[0]

    def _embed_with_chromadb(self, texts: list[str]) -> list[list[float]]:
        if self._chromadb_ef is None:
            from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

            self._chromadb_ef = DefaultEmbeddingFunction()
        result = self._chromadb_ef(texts)
        return list(result)

    def _embed_with_ollama(self, texts: list[str]) -> list[list[float]]:
        import ollama

        model = self._model or "nomic-embed-text"
        embeddings = []
        for text in texts:
            response = ollama.embeddings(model=model, prompt=text)
            embeddings.append(response["embedding"])
        return embeddings

    def _embed_with_openai(self, texts: list[str]) -> list[list[float]]:
        import openai

        model = self._model or "text-embedding-3-small"
        client = openai.OpenAI()
        response = client.embeddings.create(input=texts, model=model)
        return [item.embedding for item in response.data]
