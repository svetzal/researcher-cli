import pytest

from researcher.gateways.embedding_gateway import EmbeddingGateway


class DescribeEmbeddingGateway:
    def should_raise_for_unknown_provider_at_construction(self):
        with pytest.raises(ValueError, match="Unknown embedding provider"):
            EmbeddingGateway(provider="unknown")
