from unittest.mock import MagicMock, patch

import pytest

from researcher.gateways.chromadb_embedding_gateway import ChromaDbEmbeddingGateway


class DescribeChromaDbEmbeddingGateway:
    @pytest.fixture
    def gateway(self):
        return ChromaDbEmbeddingGateway()

    def should_lazy_init_embedding_function(self, gateway):
        assert gateway._ef is None

        mock_ef = MagicMock(return_value=[[0.1, 0.2, 0.3]])

        with patch("chromadb.utils.embedding_functions.DefaultEmbeddingFunction", return_value=mock_ef) as mock_cls:
            gateway.embed_texts(["hello"])

        mock_cls.assert_called_once()

    def should_reuse_embedding_function(self, gateway):
        mock_ef = MagicMock(return_value=[[0.1, 0.2]])

        with patch("chromadb.utils.embedding_functions.DefaultEmbeddingFunction", return_value=mock_ef) as mock_cls:
            gateway.embed_texts(["first"])
            gateway.embed_texts(["second"])

        mock_cls.assert_called_once()

    def should_return_list_of_lists_from_embed_texts(self, gateway):
        vectors = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        mock_ef = MagicMock(return_value=vectors)
        gateway._ef = mock_ef

        result = gateway.embed_texts(["a", "b"])

        assert isinstance(result, list)
        assert len(result) == 2
        assert isinstance(result[0], list)

    def should_return_single_vector_from_embed_query(self, gateway):
        mock_ef = MagicMock(return_value=[[0.1, 0.2, 0.3]])
        gateway._ef = mock_ef

        result = gateway.embed_query("hello")

        assert isinstance(result, list)
        assert not isinstance(result[0], list)
        assert result == [0.1, 0.2, 0.3]
