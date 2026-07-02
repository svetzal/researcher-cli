import pytest

from researcher.exceptions import EmbeddingError
from researcher.gateways.chromadb_embedding_gateway import ChromaDbEmbeddingGateway


class DescribeChromaDbEmbeddingGateway:
    @pytest.fixture
    def gateway(self):
        return ChromaDbEmbeddingGateway(embedding_fn=lambda texts: [[1.0, 2.0], [3.0, 4.0]])

    def should_return_embeddings_for_multiple_texts(self, gateway):
        result = gateway.embed_texts(["hello", "world"])
        assert result == [[1.0, 2.0], [3.0, 4.0]]

    def should_raise_embedding_error_on_failure(self):
        def failing_ef(texts):
            raise RuntimeError("model unavailable")

        gateway = ChromaDbEmbeddingGateway(embedding_fn=failing_ef)
        with pytest.raises(EmbeddingError, match="ChromaDB default embedding failed"):
            gateway.embed_texts(["hello"])

    def should_return_single_embedding_for_query(self):
        gateway = ChromaDbEmbeddingGateway(embedding_fn=lambda texts: [[0.5, 0.6]])
        result = gateway.embed_query("my query")
        assert result == [0.5, 0.6]

    def should_return_correct_embeddings_across_multiple_calls(self):
        results = [[[1.0]], [[2.0]]]
        call_count = [0]

        def sequential_ef(texts):
            r = results[call_count[0]]
            call_count[0] += 1
            return r

        gateway = ChromaDbEmbeddingGateway(embedding_fn=sequential_ef)
        result1 = gateway.embed_texts(["first"])
        result2 = gateway.embed_texts(["second"])
        assert result1 == [[1.0]]
        assert result2 == [[2.0]]


class DescribeChromaDbEmbeddingGatewayDefaultEmbeddingFunction:
    @pytest.mark.slow
    def should_embed_texts_with_real_default_embedding_function(self):
        pytest.importorskip("chromadb")
        gateway = ChromaDbEmbeddingGateway()
        result = gateway.embed_texts(["hello", "world"])
        assert len(result) == 2
        assert len(result[0]) == len(result[1])
        assert len(result[0]) > 0
