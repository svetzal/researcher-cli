from datetime import datetime

from researcher.models import (
    ChunkResult,
    DocumentMetadata,
    DocumentSearchResult,
    Fragment,
    FragmentForStorage,
    FragmentWithEmbedding,
    IndexingResult,
    IndexStats,
    SearchResult,
)


class DescribeDocumentMetadata:
    def should_create_with_required_fields(self):
        metadata = DocumentMetadata(
            file_path="/path/to/doc.md",
            file_name="doc.md",
            file_type="md",
            checksum="abc123",
            indexed_at=datetime(2024, 1, 1),
            fragment_count=5,
        )

        assert metadata.file_path == "/path/to/doc.md"
        assert metadata.fragment_count == 5


class DescribeFragment:
    def should_create_with_required_fields(self):
        fragment = Fragment(text="Hello world", document_path="/path/doc.md", fragment_index=0)

        assert fragment.text == "Hello world"
        assert fragment.fragment_index == 0


class DescribeFragmentForStorage:
    def should_create_with_metadata_dict(self):
        fragment = FragmentForStorage(id="f1", text="text", metadata={"key": "value"})

        assert fragment.id == "f1"
        assert fragment.metadata["key"] == "value"


class DescribeFragmentWithEmbedding:
    def should_create_with_embedding(self):
        fragment = FragmentWithEmbedding(id="f1", text="text", metadata={}, embedding=[0.1, 0.2, 0.3])

        assert len(fragment.embedding) == 3
        assert fragment.embedding[0] == 0.1


class DescribeSearchResult:
    def should_create_with_distance(self):
        result = SearchResult(
            fragment_id="f1",
            text="relevant text",
            document_path="doc.md",
            fragment_index=0,
            distance=0.1,
        )

        assert result.distance == 0.1
        assert result.document_path == "doc.md"


class DescribeDocumentSearchResult:
    def should_group_fragments_by_document(self):
        fragment = SearchResult(fragment_id="f1", text="text", document_path="doc.md", fragment_index=0, distance=0.1)
        result = DocumentSearchResult(document_path="doc.md", top_fragments=[fragment], best_distance=0.1)

        assert result.document_path == "doc.md"
        assert len(result.top_fragments) == 1


class DescribeIndexingResult:
    def should_default_errors_to_empty_list(self):
        result = IndexingResult(
            documents_indexed=5, documents_skipped=2, documents_failed=0, documents_purged=0, fragments_created=25
        )

        assert result.errors == []

    def should_accept_errors_list(self):
        result = IndexingResult(
            documents_indexed=4,
            documents_skipped=2,
            documents_failed=1,
            documents_purged=0,
            fragments_created=20,
            errors=["Failed to process doc.pdf"],
        )

        assert len(result.errors) == 1
        assert "doc.pdf" in result.errors[0]


class DescribeIndexStats:
    def should_allow_null_last_indexed(self):
        stats = IndexStats(repository_name="test", total_documents=0, total_fragments=0, last_indexed=None)

        assert stats.last_indexed is None

    def should_accept_datetime_last_indexed(self):
        dt = datetime(2024, 1, 1, 12, 0)
        stats = IndexStats(repository_name="test", total_documents=10, total_fragments=50, last_indexed=dt)

        assert stats.last_indexed == dt


class DescribeChunkResult:
    def should_hold_fragments_for_document(self):
        fragment = Fragment(text="text", document_path="/path/doc.md", fragment_index=0)
        result = ChunkResult(document_path="/path/doc.md", fragments=[fragment])

        assert result.document_path == "/path/doc.md"
        assert len(result.fragments) == 1
