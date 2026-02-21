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
        return ChromaGateway(persist_directory=temp_dir / "chroma")

    def should_create_and_count_collection(self, gateway):
        count = gateway.count("test-collection")

        assert count == 0

    def should_add_fragments_and_retrieve_count(self, gateway):
        fragments = [
            FragmentForStorage(id="f1", text="Hello world", metadata={"document_path": "/doc.md", "fragment_index": 0}),
            FragmentForStorage(
                id="f2", text="Goodbye world", metadata={"document_path": "/doc.md", "fragment_index": 1}
            ),
        ]

        gateway.add_fragments("test-collection", fragments)

        assert gateway.count("test-collection") == 2

    def should_query_and_return_results(self, gateway):
        fragments = [
            FragmentForStorage(
                id="f1", text="Python programming language", metadata={"document_path": "/doc.md", "fragment_index": 0}
            ),
        ]
        gateway.add_fragments("test-collection", fragments)

        results = gateway.query("test-collection", "programming", n_results=1)

        assert len(results) == 1
        assert results[0].fragment_id == "f1"
        assert results[0].document_path == "/doc.md"

    def should_return_empty_list_when_collection_empty(self, gateway):
        results = gateway.query("empty-collection", "anything", n_results=10)

        assert results == []

    def should_delete_fragments_by_document_path(self, gateway):
        fragments = [
            FragmentForStorage(id="f1", text="Fragment 1", metadata={"document_path": "/doc1.md", "fragment_index": 0}),
            FragmentForStorage(id="f2", text="Fragment 2", metadata={"document_path": "/doc2.md", "fragment_index": 0}),
        ]
        gateway.add_fragments("test-collection", fragments)

        gateway.delete_by_document("test-collection", "/doc1.md")

        assert gateway.count("test-collection") == 1

    def should_get_all_document_paths(self, gateway):
        fragments = [
            FragmentForStorage(id="f1", text="Fragment 1", metadata={"document_path": "/doc1.md", "fragment_index": 0}),
            FragmentForStorage(id="f2", text="Fragment 2", metadata={"document_path": "/doc2.md", "fragment_index": 0}),
            FragmentForStorage(id="f3", text="Fragment 3", metadata={"document_path": "/doc1.md", "fragment_index": 1}),
        ]
        gateway.add_fragments("test-collection", fragments)

        paths = gateway.get_all_document_paths("test-collection")

        assert len(paths) == 2
        assert "/doc1.md" in paths
        assert "/doc2.md" in paths

    def should_return_empty_paths_when_no_fragments(self, gateway):
        paths = gateway.get_all_document_paths("empty-collection")

        assert paths == []

    def should_add_fragments_with_embeddings(self, gateway):
        fragments = [
            FragmentWithEmbedding(
                id="f1",
                text="Hello world",
                metadata={"document_path": "/doc.md", "fragment_index": 0},
                embedding=[0.1] * 384,
            ),
        ]

        gateway.add_fragments_with_embeddings("test-collection", fragments)

        assert gateway.count("test-collection") == 1
