from unittest.mock import MagicMock, patch

import pytest

from researcher.gateways.embedding_gateway import EmbeddingGateway


class DescribeEmbeddingGateway:
    def should_raise_for_unknown_provider(self):
        gateway = EmbeddingGateway(provider="unknown")

        with pytest.raises(ValueError, match="Unknown embedding provider"):
            gateway.embed_texts(["test"])

    def should_embed_query_as_single_text(self):
        gateway = EmbeddingGateway(provider="chromadb")
        mock_ef = MagicMock(return_value=[[0.1, 0.2, 0.3]])

        with patch.object(gateway, "_chromadb_ef", mock_ef):
            result = gateway.embed_query("test query")

        assert result == [0.1, 0.2, 0.3]

    def should_use_chromadb_default_embedding_function(self):
        gateway = EmbeddingGateway(provider="chromadb")
        mock_ef = MagicMock(return_value=[[0.1, 0.2], [0.3, 0.4]])
        gateway._chromadb_ef = mock_ef

        result = gateway.embed_texts(["text1", "text2"])

        mock_ef.assert_called_once_with(["text1", "text2"])
        assert len(result) == 2
