from typing import Any

from researcher.exceptions import EmbeddingError
from researcher.gateways.embedding_gateway import EmbeddingGateway
from researcher.gateways.error_wrapper import wrap_gateway_error

_wrap_embedding_error = wrap_gateway_error(EmbeddingError)


class OpenAIEmbeddingGateway(EmbeddingGateway):
    """Thin wrapper around the OpenAI embeddings API."""

    def __init__(self, model: str, client: Any = None) -> None:
        self._model = model
        self._client = client

    @_wrap_embedding_error("OpenAI embedding failed for model '{self._model}': {e}")
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if self._client is not None:
            client = self._client
        else:
            import openai

            client = openai.OpenAI()
        response = client.embeddings.create(input=texts, model=self._model)
        return [item.embedding for item in response.data]
