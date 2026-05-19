import pytest

from researcher.exceptions import EmbeddingError
from researcher.gateways.ollama_embedding_gateway import OllamaEmbeddingGateway


class DescribeOllamaEmbeddingGateway:
    def should_return_embeddings_for_multiple_texts(self):
        embedding_map = {"hello": [1.0, 2.0], "world": [3.0, 4.0]}

        class _Fake:
            def embeddings(self, model, prompt):
                return {"embedding": embedding_map[prompt]}

        gateway = OllamaEmbeddingGateway(model="nomic-embed-text", client=_Fake())
        result = gateway.embed_texts(["hello", "world"])
        assert result == [[1.0, 2.0], [3.0, 4.0]]

    def should_call_ollama_with_correct_model_and_prompt(self):
        vectors = {"alpha": [0.1, 0.2], "beta": [0.3, 0.4]}

        class _Fake:
            def embeddings(self, model, prompt):
                return {"embedding": vectors[prompt]}

        gateway = OllamaEmbeddingGateway(model="nomic-embed-text", client=_Fake())
        result = gateway.embed_texts(["alpha", "beta"])
        assert result == [[0.1, 0.2], [0.3, 0.4]]

    def should_raise_embedding_error_on_failure(self):
        class _Fake:
            def embeddings(self, model, prompt):
                raise ConnectionError("connection refused")

        gateway = OllamaEmbeddingGateway(model="nomic-embed-text", client=_Fake())
        with pytest.raises(EmbeddingError, match="nomic-embed-text"):
            gateway.embed_texts(["hello"])

    def should_store_model_name_used_in_api_calls(self):
        class _Fake:
            def embeddings(self, model, prompt):
                return {"embedding": [0.5] if model == "mxbai-embed-large" else [0.0]}

        gateway = OllamaEmbeddingGateway(model="mxbai-embed-large", client=_Fake())
        result = gateway.embed_texts(["test"])
        assert result == [[0.5]]
