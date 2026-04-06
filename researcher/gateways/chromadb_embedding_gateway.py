from typing import Any

from researcher.exceptions import EmbeddingError
from researcher.gateways.embedding_gateway import EmbeddingGateway


class ChromaDbEmbeddingGateway(EmbeddingGateway):
    """Thin wrapper around chromadb's default embedding function."""

    def __init__(self) -> None:
        self._ef: Any = None

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        try:
            if self._ef is None:
                from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

                self._ef = DefaultEmbeddingFunction()
            return list(self._ef(texts))
        except Exception as e:
            raise EmbeddingError(f"ChromaDB default embedding failed: {e}") from e
