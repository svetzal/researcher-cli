import sys
from unittest.mock import MagicMock, call, patch

import pytest

from researcher.exceptions import EmbeddingError
from researcher.gateways.ollama_embedding_gateway import OllamaEmbeddingGateway


@pytest.fixture(autouse=True)
def mock_ollama_module():
    """Inject a fake ollama module so tests run without the optional dependency."""
    mock_module = MagicMock()
    with patch.dict(sys.modules, {"ollama": mock_module}):
        yield mock_module


class DescribeOllamaEmbeddingGateway:
    @pytest.fixture
    def gateway(self):
        return OllamaEmbeddingGateway(model="nomic-embed-text")

    def should_return_embeddings_for_multiple_texts(self, gateway, mock_ollama_module):
        mock_ollama_module.embeddings.side_effect = [
            {"embedding": [1.0, 2.0]},
            {"embedding": [3.0, 4.0]},
        ]

        result = gateway.embed_texts(["hello", "world"])

        assert result == [[1.0, 2.0], [3.0, 4.0]]

    def should_call_ollama_with_correct_model_and_prompt(self, gateway, mock_ollama_module):
        mock_ollama_module.embeddings.return_value = {"embedding": [0.1, 0.2]}

        gateway.embed_texts(["alpha", "beta"])

        assert mock_ollama_module.embeddings.call_args_list == [
            call(model="nomic-embed-text", prompt="alpha"),
            call(model="nomic-embed-text", prompt="beta"),
        ]

    def should_raise_embedding_error_on_failure(self, gateway, mock_ollama_module):
        mock_ollama_module.embeddings.side_effect = ConnectionError("connection refused")

        with pytest.raises(EmbeddingError, match="nomic-embed-text"):
            gateway.embed_texts(["hello"])

    def should_store_model_name_used_in_api_calls(self, mock_ollama_module):
        gateway = OllamaEmbeddingGateway(model="mxbai-embed-large")
        mock_ollama_module.embeddings.return_value = {"embedding": [0.5]}

        gateway.embed_texts(["test"])

        mock_ollama_module.embeddings.assert_called_once_with(model="mxbai-embed-large", prompt="test")
