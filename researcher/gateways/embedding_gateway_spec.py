import pytest

from researcher.gateways.embedding_gateway import EmbeddingGateway


class DescribeEmbeddingGateway:
    def should_raise_for_unknown_provider(self):
        gateway = EmbeddingGateway(provider="unknown")

        with pytest.raises(ValueError, match="Unknown embedding provider"):
            gateway.embed_texts(["test"])
