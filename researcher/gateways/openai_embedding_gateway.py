from researcher.exceptions import EmbeddingError


class OpenAIEmbeddingGateway:
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

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]
