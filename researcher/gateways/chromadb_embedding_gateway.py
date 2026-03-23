from typing import Any


class ChromaDbEmbeddingGateway:
    """Thin wrapper around chromadb's default embedding function."""

    def __init__(self) -> None:
        self._ef: Any = None

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if self._ef is None:
            from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

            self._ef = DefaultEmbeddingFunction()
        return list(self._ef(texts))

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]
