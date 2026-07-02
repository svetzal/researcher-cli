from types import SimpleNamespace

import pytest

from researcher.exceptions import EmbeddingError
from researcher.gateways.openai_embedding_gateway import OpenAIEmbeddingGateway


def _make_response(vectors: list[list[float]]):
    return SimpleNamespace(data=[SimpleNamespace(embedding=v) for v in vectors])


class DescribeOpenAIEmbeddingGateway:
    @pytest.fixture
    def gateway(self):
        fake_client = SimpleNamespace(
            embeddings=SimpleNamespace(create=lambda input, model: _make_response([[1.0, 2.0], [3.0, 4.0]]))
        )
        return OpenAIEmbeddingGateway(model="text-embedding-3-small", client=fake_client)

    def should_return_embeddings_for_multiple_texts(self, gateway):
        result = gateway.embed_texts(["hello", "world"])
        assert result == [[1.0, 2.0], [3.0, 4.0]]

    def should_call_openai_with_correct_model_and_input(self):
        calls = []

        def create(input, model):
            calls.append({"input": input, "model": model})
            return _make_response([[0.1, 0.2, 0.3]])

        fake_client = SimpleNamespace(embeddings=SimpleNamespace(create=create))
        gateway = OpenAIEmbeddingGateway(model="text-embedding-3-small", client=fake_client)
        result = gateway.embed_texts(["my text"])
        assert result == [[0.1, 0.2, 0.3]]
        assert calls[0]["input"] == ["my text"]
        assert calls[0]["model"] == "text-embedding-3-small"

    def should_raise_embedding_error_on_failure(self):
        def create(input, model):
            raise RuntimeError("API error")

        fake_client = SimpleNamespace(embeddings=SimpleNamespace(create=create))
        gateway = OpenAIEmbeddingGateway(model="text-embedding-3-small", client=fake_client)
        with pytest.raises(EmbeddingError, match="text-embedding-3-small"):
            gateway.embed_texts(["hello"])

    def should_store_model_name_used_in_api_calls(self):
        calls = []

        def create(input, model):
            calls.append(model)
            return _make_response([[0.5, 0.6]])

        fake_client = SimpleNamespace(embeddings=SimpleNamespace(create=create))
        gateway = OpenAIEmbeddingGateway(model="text-embedding-ada-002", client=fake_client)
        result = gateway.embed_texts(["query"])
        assert result == [[0.5, 0.6]]
        assert calls[0] == "text-embedding-ada-002"


class DescribeOpenAIEmbeddingGatewayCreateClient:
    def should_return_openai_client(self, monkeypatch):
        openai = pytest.importorskip("openai")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        gateway = OpenAIEmbeddingGateway(model="text-embedding-3-small")
        client = gateway._create_client()
        assert isinstance(client, openai.OpenAI)
        assert hasattr(client, "embeddings")
