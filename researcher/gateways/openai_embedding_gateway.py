from researcher.exceptions import EmbeddingError
from researcher.gateways.embedding_gateway import LazyClientEmbeddingGateway
from researcher.gateways.error_wrapper import wrap_gateway_error

_wrap_embedding_error = wrap_gateway_error(EmbeddingError)


class OpenAIEmbeddingGateway(LazyClientEmbeddingGateway):
    def _create_client(self):
        import openai

        return openai.OpenAI()

    @_wrap_embedding_error("OpenAI embedding failed for model '{self._model}': {e}")
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        client = self._resolve_client()
        response = client.embeddings.create(input=texts, model=self._model)
        return [item.embedding for item in response.data]
