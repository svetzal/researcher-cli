import tempfile
from pathlib import Path

import pytest

from researcher.gateways.chroma_gateway import ChromaGateway
from researcher.models import FragmentForStorage, FragmentWithEmbedding


class DescribeChromaGateway:
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    @pytest.fixture
    def gateway(self, temp_dir):
        return ChromaGateway(persist_directory=temp_dir)

    def should_add_and_count_fragments(self, gateway):
        fragments = [
            FragmentForStorage(id="f1", text="hello world", metadata={"document_path": "/doc.md"}),
            FragmentForStorage(id="f2", text="foo bar", metadata={"document_path": "/doc.md"}),
        ]

        gateway.add_fragments("test-collection", fragments)

        assert gateway.count("test-collection") == 2

    def should_upsert_without_duplicates(self, gateway):
        fragment = FragmentForStorage(id="f1", text="hello", metadata={"document_path": "/doc.md"})

        gateway.add_fragments("test-collection", [fragment])
        gateway.add_fragments("test-collection", [fragment])

        assert gateway.count("test-collection") == 1

    def should_add_fragments_with_embeddings_and_query(self, gateway):
        fragments = [
            FragmentWithEmbedding(
                id="f1",
                text="alpha",
                metadata={"document_path": "/a.md", "fragment_index": 0},
                embedding=[1.0, 0.0, 0.0],
            ),
            FragmentWithEmbedding(
                id="f2",
                text="beta",
                metadata={"document_path": "/b.md", "fragment_index": 0},
                embedding=[0.0, 1.0, 0.0],
            ),
        ]

        gateway.add_fragments_with_embeddings("embed-collection", fragments)
        results = gateway.query_with_embedding("embed-collection", [1.0, 0.0, 0.0], n_results=1)

        assert len(results) == 1
        assert results[0].text == "alpha"

    def should_delete_by_document_path(self, gateway):
        fragments = [
            FragmentForStorage(id="f1", text="from doc a", metadata={"document_path": "/a.md"}),
            FragmentForStorage(id="f2", text="from doc b", metadata={"document_path": "/b.md"}),
        ]
        gateway.add_fragments("test-collection", fragments)

        gateway.delete_by_document("test-collection", "/a.md")

        assert gateway.count("test-collection") == 1

    def should_delete_collection(self, gateway):
        fragment = FragmentForStorage(id="f1", text="hello", metadata={"document_path": "/doc.md"})
        gateway.add_fragments("test-collection", [fragment])

        gateway.delete_collection("test-collection")

        assert gateway.count("test-collection") == 0

    def should_return_metadata_batch(self, gateway):
        fragments = [
            FragmentForStorage(id=f"f{i}", text=f"text {i}", metadata={"document_path": f"/doc{i}.md"})
            for i in range(3)
        ]
        gateway.add_fragments("test-collection", fragments)

        batch = gateway.get_metadata_batch("test-collection", limit=2, offset=0)

        assert len(batch) == 2

    def should_return_empty_results_for_empty_collection(self, gateway):
        results = gateway.query_with_embedding("empty-collection", [1.0, 0.0, 0.0], n_results=5)

        assert results == []
