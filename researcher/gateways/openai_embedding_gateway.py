from researcher.exceptions import EmbeddingError
from researcher.gateways.embedding_gateway import EmbeddingGateway
from researcher.gateways.error_wrapper import wrap_gateway_error

_wrap_embedding_error = wrap_gateway_error(EmbeddingError)


class OpenAIEmbeddingGateway(EmbeddingGateway):
    """Thin wrapper around the OpenAI embeddings API."""

    def __init__(self, model: str) -> None:
        self._model = model

    @_wrap_embedding_error("OpenAI embedding failed for model '{self._model}': {e}")
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        import openai

        client = openai.OpenAI()
        response = client.embeddings.create(input=texts, model=self._model)
        return [item.embedding for item in response.data]
