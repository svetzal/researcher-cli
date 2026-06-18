from typing import Any

from researcher.gateways.embedding_gateway import EmbeddingGateway
from researcher.gateways.error_wrapper import wrap_embedding_error


class ChromaDbEmbeddingGateway(EmbeddingGateway):
    def __init__(self, embedding_fn: Any = None) -> None:
        self._embedding_fn: Any = embedding_fn

    @wrap_embedding_error("ChromaDB default embedding failed: {e}")
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if self._embedding_fn is None:
            from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

            self._embedding_fn = DefaultEmbeddingFunction()
        return list(self._embedding_fn(texts))
