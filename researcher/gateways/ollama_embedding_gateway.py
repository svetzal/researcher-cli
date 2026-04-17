from researcher.exceptions import EmbeddingError
from researcher.gateways.embedding_gateway import EmbeddingGateway
from researcher.gateways.error_wrapper import wrap_gateway_error

_wrap_embedding_error = wrap_gateway_error(EmbeddingError)


class OllamaEmbeddingGateway(EmbeddingGateway):
    """Thin wrapper around the ollama embeddings API."""

    def __init__(self, model: str) -> None:
        self._model = model

    @_wrap_embedding_error("Ollama embedding failed for model '{self._model}': {e}")
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        import ollama

        embeddings = []
        for text in texts:
            response = ollama.embeddings(model=self._model, prompt=text)
            embeddings.append(response["embedding"])
        return embeddings
