from researcher.exceptions import EmbeddingError
from researcher.gateways.embedding_gateway import EmbeddingGateway


class OpenAIEmbeddingGateway(EmbeddingGateway):
    """Thin wrapper around the OpenAI embeddings API."""

    def __init__(self, model: str) -> None:
        self._model = model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        import openai

        try:
            client = openai.OpenAI()
            response = client.embeddings.create(input=texts, model=self._model)
            return [item.embedding for item in response.data]
        except Exception as e:
            raise EmbeddingError(f"OpenAI embedding failed for model '{self._model}': {e}") from e
