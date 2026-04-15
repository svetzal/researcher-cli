from unittest.mock import MagicMock, patch

import pytest

from researcher.exceptions import EmbeddingError
from researcher.gateways.chromadb_embedding_gateway import ChromaDbEmbeddingGateway


class DescribeChromaDbEmbeddingGateway:
    @pytest.fixture
    def gateway(self):
        return ChromaDbEmbeddingGateway()

    def should_return_embeddings_for_multiple_texts(self, gateway):
        expected = [[1.0, 2.0], [3.0, 4.0]]
        mock_ef = MagicMock(return_value=expected)

        with patch(
            "chromadb.utils.embedding_functions.DefaultEmbeddingFunction",
            return_value=mock_ef,
        ):
            result = gateway.embed_texts(["hello", "world"])

        assert result == expected

    def should_raise_embedding_error_on_failure(self, gateway):
        mock_ef = MagicMock(side_effect=RuntimeError("model unavailable"))

        with (
            patch(
                "chromadb.utils.embedding_functions.DefaultEmbeddingFunction",
                return_value=mock_ef,
            ),
            pytest.raises(EmbeddingError, match="ChromaDB default embedding failed"),
        ):
            gateway.embed_texts(["hello"])

    def should_return_single_embedding_for_query(self, gateway):
        expected = [[0.5, 0.6]]
        mock_ef = MagicMock(return_value=expected)

        with patch(
            "chromadb.utils.embedding_functions.DefaultEmbeddingFunction",
            return_value=mock_ef,
        ):
            result = gateway.embed_query("my query")

        assert result == [0.5, 0.6]

    def should_initialize_embedding_function_only_once(self, gateway):
        mock_ef = MagicMock(return_value=[[1.0]])

        with patch(
            "chromadb.utils.embedding_functions.DefaultEmbeddingFunction",
            return_value=mock_ef,
        ) as mock_cls:
            gateway.embed_texts(["first"])
            gateway.embed_texts(["second"])

        mock_cls.assert_called_once()
