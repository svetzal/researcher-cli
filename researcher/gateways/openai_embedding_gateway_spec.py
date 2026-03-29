import sys
from unittest.mock import MagicMock, patch

import pytest

from researcher.gateways.openai_embedding_gateway import OpenAIEmbeddingGateway


class DescribeOpenAIEmbeddingGateway:
    @pytest.fixture
    def gateway(self):
        return OpenAIEmbeddingGateway(model="test-model")

    @pytest.fixture(autouse=True)
    def mock_openai_module(self):
        mock_openai = MagicMock()
        with patch.dict(sys.modules, {"openai": mock_openai}):
            yield mock_openai

    def should_call_openai_with_correct_model_and_batch(self, gateway, mock_openai_module):
        mock_item = MagicMock()
        mock_item.embedding = [0.1, 0.2]
        mock_response = MagicMock()
        mock_response.data = [mock_item, mock_item]
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai_module.OpenAI.return_value = mock_client

        gateway.embed_texts(["a", "b"])

        mock_client.embeddings.create.assert_called_once_with(input=["a", "b"], model="test-model")

    def should_extract_embeddings_from_response_data(self, gateway, mock_openai_module):
        items = []
        for vec in [[1.0, 0.0], [0.0, 1.0]]:
            item = MagicMock()
            item.embedding = vec
            items.append(item)
        mock_response = MagicMock()
        mock_response.data = items
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai_module.OpenAI.return_value = mock_client

        result = gateway.embed_texts(["x", "y"])

        assert result == [[1.0, 0.0], [0.0, 1.0]]

    def should_return_single_vector_from_embed_query(self, gateway, mock_openai_module):
        mock_item = MagicMock()
        mock_item.embedding = [0.3, 0.7, 0.1]
        mock_response = MagicMock()
        mock_response.data = [mock_item]
        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai_module.OpenAI.return_value = mock_client

        result = gateway.embed_query("question")

        assert result == [0.3, 0.7, 0.1]
        assert not isinstance(result[0], list)
