from typing import Any

from researcher.exceptions import EmbeddingError
from researcher.gateways.embedding_gateway import EmbeddingGateway
from researcher.gateways.error_wrapper import wrap_gateway_error

_wrap_embedding_error = wrap_gateway_error(EmbeddingError)


class ChromaDbEmbeddingGateway(EmbeddingGateway):
    def __init__(self, embedding_fn: Any = None) -> None:
        self._embedding_fn: Any = embedding_fn

    @_wrap_embedding_error("ChromaDB default embedding failed: {e}")
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if self._embedding_fn is None:
            from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

            self._embedding_fn = DefaultEmbeddingFunction()
        return list(self._embedding_fn(texts))
