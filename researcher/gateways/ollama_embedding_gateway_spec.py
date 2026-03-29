import sys
from unittest.mock import MagicMock, patch

import pytest

from researcher.gateways.ollama_embedding_gateway import OllamaEmbeddingGateway


class DescribeOllamaEmbeddingGateway:
    @pytest.fixture
    def gateway(self):
        return OllamaEmbeddingGateway(model="test-model")

    @pytest.fixture(autouse=True)
    def mock_ollama_module(self):
        mock_ollama = MagicMock()
        with patch.dict(sys.modules, {"ollama": mock_ollama}):
            yield mock_ollama

    def should_call_ollama_with_correct_model(self, gateway, mock_ollama_module):
        mock_ollama_module.embeddings.return_value = {"embedding": [0.1, 0.2, 0.3]}

        gateway.embed_texts(["hello"])

        mock_ollama_module.embeddings.assert_called_once_with(model="test-model", prompt="hello")

    def should_embed_texts_sequentially(self, gateway, mock_ollama_module):
        mock_ollama_module.embeddings.return_value = {"embedding": [0.1, 0.2]}

        gateway.embed_texts(["a", "b", "c"])

        assert mock_ollama_module.embeddings.call_count == 3

    def should_return_embeddings_in_order(self, gateway, mock_ollama_module):
        mock_ollama_module.embeddings.side_effect = [
            {"embedding": [1.0, 0.0]},
            {"embedding": [0.0, 1.0]},
            {"embedding": [0.5, 0.5]},
        ]

        result = gateway.embed_texts(["x", "y", "z"])

        assert result[0] == [1.0, 0.0]
        assert result[1] == [0.0, 1.0]
        assert result[2] == [0.5, 0.5]

    def should_return_single_vector_from_embed_query(self, gateway, mock_ollama_module):
        mock_ollama_module.embeddings.return_value = {"embedding": [0.1, 0.2, 0.3]}

        result = gateway.embed_query("test query")

        assert result == [0.1, 0.2, 0.3]
        assert not isinstance(result[0], list)
