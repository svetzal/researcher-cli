from researcher.exceptions import EmbeddingError


class OllamaEmbeddingGateway:
    """Thin wrapper around the ollama embeddings API."""

    def __init__(self, model: str) -> None:
        self._model = model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        import ollama

        embeddings = []
        for text in texts:
            try:
                response = ollama.embeddings(model=self._model, prompt=text)
                embeddings.append(response["embedding"])
            except Exception as e:
                raise EmbeddingError(f"Ollama embedding failed for model '{self._model}': {e}") from e
        return embeddings

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]
