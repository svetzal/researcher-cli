from typing import Any

from researcher.exceptions import EmbeddingError
from researcher.gateways.embedding_gateway import EmbeddingGateway
from researcher.gateways.error_wrapper import wrap_gateway_error

_wrap_embedding_error = wrap_gateway_error(EmbeddingError)


class OllamaEmbeddingGateway(EmbeddingGateway):
    def __init__(self, model: str, client: Any = None) -> None:
        self._model = model
        self._client = client

    @_wrap_embedding_error("Ollama embedding failed for model '{self._model}': {e}")
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if self._client is not None:
            client = self._client
        else:
            import ollama

            client = ollama
        embeddings = []
        for text in texts:
            response = client.embeddings(model=self._model, prompt=text)
            embeddings.append(response["embedding"])
        return embeddings
