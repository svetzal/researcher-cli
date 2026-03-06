from collections.abc import Callable
from typing import Any

from researcher.embedding_providers import resolve_embedding_config


class EmbeddingGateway:
    """Provides embedding generation with multiple backend support."""

    def __init__(self, provider: str = "chromadb", model: str | None = None):
        self._config = resolve_embedding_config(provider, model)
        self._chromadb_ef: Any = None
        self._dispatch: dict[str, Callable[[list[str]], list[list[float]]]] = {
            "chromadb": self._embed_with_chromadb,
            "ollama": self._embed_with_ollama,
            "openai": self._embed_with_openai,
        }

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        embed_fn = self._dispatch.get(self._config.provider)
        if embed_fn is None:
            raise ValueError(f"Unsupported embedding provider: {self._config.provider}")
        return embed_fn(texts)

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

        embeddings = []
        for text in texts:
            response = ollama.embeddings(model=self._config.model, prompt=text)
            embeddings.append(response["embedding"])
        return embeddings

    def _embed_with_openai(self, texts: list[str]) -> list[list[float]]:
        import openai

        client = openai.OpenAI()
        response = client.embeddings.create(input=texts, model=self._config.model)
        return [item.embedding for item in response.data]
