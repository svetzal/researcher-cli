from typing import Any

from researcher.exceptions import EmbeddingError
from researcher.gateways.embedding_gateway import EmbeddingGateway
from researcher.gateways.error_wrapper import wrap_gateway_error

_wrap_embedding_error = wrap_gateway_error(EmbeddingError)


class ChromaDbEmbeddingGateway(EmbeddingGateway):
    """Thin wrapper around chromadb's default embedding function."""

    def __init__(self) -> None:
        self._ef: Any = None

    @_wrap_embedding_error("ChromaDB default embedding failed: {e}")
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if self._ef is None:
            from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

            self._ef = DefaultEmbeddingFunction()
        return list(self._ef(texts))
