import sys
from unittest.mock import MagicMock, patch

import pytest

from researcher.exceptions import EmbeddingError
from researcher.gateways.openai_embedding_gateway import OpenAIEmbeddingGateway


@pytest.fixture(autouse=True)
def mock_openai_module():
    """Inject a fake openai module so tests run without the optional dependency."""
    mock_module = MagicMock()
    with patch.dict(sys.modules, {"openai": mock_module}):
        yield mock_module


def _make_response(vectors: list[list[float]]) -> MagicMock:
    response = MagicMock()
    response.data = [MagicMock(embedding=v) for v in vectors]
    return response


class DescribeOpenAIEmbeddingGateway:
    @pytest.fixture
    def gateway(self):
        return OpenAIEmbeddingGateway(model="text-embedding-3-small")

    def should_return_embeddings_for_multiple_texts(self, gateway, mock_openai_module):
        vectors = [[1.0, 2.0], [3.0, 4.0]]
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = _make_response(vectors)
        mock_openai_module.OpenAI.return_value = mock_client

        result = gateway.embed_texts(["hello", "world"])

        assert result == vectors

    def should_call_openai_with_correct_model_and_input(self, gateway, mock_openai_module):
        expected_vector = [0.1, 0.2, 0.3]
        mock_client = MagicMock()
        mock_client.embeddings.create.side_effect = lambda input, model: (
            _make_response([expected_vector])
            if input == ["my text"] and model == "text-embedding-3-small"
            else _make_response([[0.0]])
        )
        mock_openai_module.OpenAI.return_value = mock_client

        result = gateway.embed_texts(["my text"])

        assert result == [expected_vector]

    def should_raise_embedding_error_on_failure(self, gateway, mock_openai_module):
        mock_client = MagicMock()
        mock_client.embeddings.create.side_effect = RuntimeError("API error")
        mock_openai_module.OpenAI.return_value = mock_client

        with pytest.raises(EmbeddingError, match="text-embedding-3-small"):
            gateway.embed_texts(["hello"])

    def should_store_model_name_used_in_api_calls(self, mock_openai_module):
        gateway = OpenAIEmbeddingGateway(model="text-embedding-ada-002")
        expected_vector = [0.5, 0.6]
        mock_client = MagicMock()
        mock_client.embeddings.create.side_effect = lambda input, model: (
            _make_response([expected_vector]) if model == "text-embedding-ada-002" else _make_response([[0.0]])
        )
        mock_openai_module.OpenAI.return_value = mock_client

        result = gateway.embed_texts(["query"])

        assert result == [expected_vector]
