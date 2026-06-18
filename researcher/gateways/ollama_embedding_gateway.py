from researcher.gateways.embedding_gateway import LazyClientEmbeddingGateway
from researcher.gateways.error_wrapper import wrap_embedding_error


class OllamaEmbeddingGateway(LazyClientEmbeddingGateway):
    def _create_client(self):
        import ollama

        return ollama

    @wrap_embedding_error("Ollama embedding failed for model '{self._model}': {e}")
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        client = self._resolve_client()
        embeddings = []
        for text in texts:
            response = client.embeddings(model=self._model, prompt=text)
            embeddings.append(response["embedding"])
        return embeddings
