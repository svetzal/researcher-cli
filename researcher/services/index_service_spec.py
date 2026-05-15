from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

from researcher.config import RepositoryConfig
from researcher.exceptions import DocumentConversionError
from researcher.gateways.checksum_gateway import ChecksumGateway
from researcher.gateways.chroma_gateway import ChromaGateway
from researcher.gateways.docling_gateway import DoclingGateway
from researcher.gateways.embedding_gateway import EmbeddingGateway
from researcher.gateways.filesystem_gateway import FilesystemGateway
from researcher.services.index_service import IndexService


class _FakeChunk:
    def __init__(self, text: str):
        self.text = text


class DescribeIndexService:
    @pytest.fixture
    def mock_filesystem(self):
        return Mock(spec=FilesystemGateway)

    @pytest.fixture
    def mock_docling(self):
        return Mock(spec=DoclingGateway)

    @pytest.fixture
    def mock_embedding(self):
        return Mock(spec=EmbeddingGateway)

    @pytest.fixture
    def mock_chroma(self):
        m = Mock(spec=ChromaGateway)
        m.count.return_value = 0
        return m

    @pytest.fixture
    def mock_checksums(self):
        m = Mock(spec=ChecksumGateway)
        m.load.return_value = {}
        return m

    @pytest.fixture
    def service(self, mock_filesystem, mock_docling, mock_embedding, mock_chroma, mock_checksums):
        return IndexService(
            filesystem_gateway=mock_filesystem,
            docling_gateway=mock_docling,
            embedding_gateway=mock_embedding,
            chroma_gateway=mock_chroma,
            repo_name="test-repo",
            checksum_gateway=mock_checksums,
        )

    @pytest.fixture
    def repo_config(self):
        return RepositoryConfig(name="test-repo", path="/tmp/docs", embedding_provider="chromadb")

    def should_skip_unchanged_files(
        self, service, mock_filesystem, mock_docling, mock_chroma, mock_checksums, repo_config
    ):
        file_path = Path("/tmp/docs/doc.md")
        mock_filesystem.list_files.return_value = [file_path]
        mock_filesystem.compute_checksum.return_value = "abc123"
        mock_checksums.load.return_value = {str(file_path): "abc123"}

        result = service.index_repository(repo_config)

        assert result.documents_skipped == 1
        assert result.documents_indexed == 0

    def should_reindex_unchanged_files_when_force_is_true(
        self, service, mock_filesystem, mock_docling, mock_chroma, mock_checksums, repo_config
    ):
        file_path = Path("/tmp/docs/doc.md")
        mock_filesystem.list_files.return_value = [file_path]
        mock_filesystem.compute_checksum.return_value = "abc123"
        mock_filesystem.read_file.return_value = "Some text"
        mock_checksums.load.return_value = {str(file_path): "abc123"}

        result = service.index_repository(repo_config, force=True)

        assert result.documents_skipped == 0
        assert result.documents_indexed == 1

    def should_pass_exclude_patterns_to_list_files(
        self, service, mock_filesystem, mock_docling, mock_chroma, mock_checksums
    ):
        repo_config = RepositoryConfig(
            name="test-repo",
            path="/tmp/docs",
            embedding_provider="chromadb",
            exclude_patterns=["node_modules", ".*"],
        )
        captured: list[tuple] = []

        def _capture(file_types, patterns):
            captured.append((file_types, patterns))
            return []

        mock_filesystem.list_files.side_effect = _capture

        service.index_repository(repo_config)

        assert len(captured) == 1
        assert captured[0] == (repo_config.file_types, ["node_modules", ".*"])

    def should_pass_default_exclude_patterns_to_list_files(
        self, service, mock_filesystem, mock_docling, mock_chroma, mock_checksums, repo_config
    ):
        captured: list[tuple] = []

        def _capture(file_types, patterns):
            captured.append((file_types, patterns))
            return []

        mock_filesystem.list_files.side_effect = _capture

        service.index_repository(repo_config)

        assert len(captured) == 1
        assert captured[0] == (repo_config.file_types, [".*"])

    def should_index_new_files(self, service, mock_filesystem, mock_docling, mock_chroma, mock_checksums, repo_config):
        file_path = Path("/tmp/docs/doc.pdf")
        mock_filesystem.list_files.return_value = [file_path]
        mock_filesystem.compute_checksum.return_value = "new_checksum"
        mock_docling.convert.return_value = "mock_document"
        mock_docling.chunk.return_value = [_FakeChunk("Hello world")]

        result = service.index_repository(repo_config)

        assert result.documents_indexed == 1
        assert result.fragments_created == 1

    def should_delete_old_fragments_before_reindexing(
        self, service, mock_filesystem, mock_docling, mock_chroma, mock_checksums, repo_config
    ):
        file_path = Path("/tmp/docs/doc.pdf")
        mock_filesystem.list_files.return_value = [file_path]
        mock_filesystem.compute_checksum.return_value = "new_checksum"
        mock_docling.convert.return_value = "mock_document"
        mock_docling.chunk.return_value = [_FakeChunk("Updated text")]
        mock_checksums.load.return_value = {str(file_path): "old_checksum"}

        result = service.index_repository(repo_config)

        assert result.documents_indexed == 1

    def should_bypass_docling_for_plain_text_files(
        self, service, mock_filesystem, mock_docling, mock_chroma, mock_checksums, repo_config
    ):
        file_path = Path("/tmp/docs/notes.txt")
        mock_filesystem.list_files.return_value = [file_path]
        mock_filesystem.compute_checksum.return_value = "new_checksum"
        mock_filesystem.read_file.return_value = "Some plain text content"

        result = service.index_repository(repo_config)

        assert result.documents_indexed == 1

    def should_bypass_docling_for_markdown_files(
        self, service, mock_filesystem, mock_docling, mock_chroma, mock_checksums, repo_config
    ):
        file_path = Path("/tmp/docs/readme.md")
        mock_filesystem.list_files.return_value = [file_path]
        mock_filesystem.compute_checksum.return_value = "new_checksum"
        mock_filesystem.read_file.return_value = "# Heading\n\nSome markdown content"

        result = service.index_repository(repo_config)

        assert result.documents_indexed == 1

    def should_use_docling_for_pdf_files(
        self, service, mock_filesystem, mock_docling, mock_chroma, mock_checksums, repo_config
    ):
        file_path = Path("/tmp/docs/report.pdf")
        mock_filesystem.list_files.return_value = [file_path]
        mock_filesystem.compute_checksum.return_value = "new_checksum"
        mock_docling.convert.return_value = "mock_document"
        mock_docling.chunk.return_value = [_FakeChunk("PDF content")]

        result = service.index_repository(repo_config)

        assert result.documents_indexed == 1

    def should_record_errors_without_reraise(
        self, service, mock_filesystem, mock_docling, mock_chroma, mock_checksums, repo_config
    ):
        file_path = Path("/tmp/docs/bad.pdf")
        mock_filesystem.list_files.return_value = [file_path]
        mock_filesystem.compute_checksum.return_value = "checksum"
        mock_docling.convert.side_effect = DocumentConversionError("Conversion failed")
        mock_checksums.load.return_value = {}

        result = service.index_repository(repo_config)

        assert result.documents_failed == 1
        assert len(result.errors) == 1
        assert "Conversion failed" in result.errors[0]

    def should_use_external_embeddings_for_non_chromadb_provider(
        self, service, mock_filesystem, mock_docling, mock_embedding, mock_chroma, mock_checksums, repo_config
    ):
        repo_config = RepositoryConfig(name="test-repo", path="/tmp/docs", embedding_provider="ollama")
        file_path = Path("/tmp/docs/doc.pdf")
        mock_filesystem.list_files.return_value = [file_path]
        mock_filesystem.compute_checksum.return_value = "checksum"
        mock_docling.convert.return_value = "mock_document"
        mock_docling.chunk.return_value = [_FakeChunk("Hello world")]
        mock_embedding.embed_texts.return_value = [[0.1, 0.2, 0.3]]

        result = service.index_repository(repo_config)

        assert result.documents_indexed == 1
        assert result.fragments_created == 1

    def should_purge_excluded_documents_during_indexing(
        self, service, mock_filesystem, mock_docling, mock_chroma, mock_checksums
    ):
        """Documents indexed before exclude patterns were configured should be purged on next index."""
        repo_config = RepositoryConfig(
            name="test-repo",
            path="/tmp/docs",
            embedding_provider="chromadb",
            exclude_patterns=["node_modules"],
        )
        mock_checksums.load.return_value = {
            "/tmp/docs/readme.md": "aaa",
            "/tmp/docs/node_modules/dep.md": "bbb",
        }
        mock_chroma.count.return_value = 2
        mock_chroma.get_metadata_batch.return_value = [
            {"document_path": "/tmp/docs/readme.md"},
            {"document_path": "/tmp/docs/node_modules/dep.md"},
        ]
        mock_filesystem.list_files.return_value = [Path("/tmp/docs/readme.md")]
        mock_filesystem.compute_checksum.return_value = "aaa"

        deleted_docs: list[tuple] = []
        mock_chroma.delete_by_document.side_effect = lambda coll, path: deleted_docs.append((coll, path))
        saved_checksum_maps: list[dict] = []
        mock_checksums.save.side_effect = lambda cs: saved_checksum_maps.append(dict(cs))

        result = service.index_repository(repo_config)

        assert result.documents_purged == 1
        assert deleted_docs == [("documents", "/tmp/docs/node_modules/dep.md")]
        # The purged document should be removed from the saved checksums
        assert "/tmp/docs/node_modules/dep.md" not in saved_checksum_maps[-1]

    def should_return_skipped_in_process_file_for_unchanged_checksum(self, service, mock_filesystem, mock_chroma):
        file_path = Path("/tmp/docs/doc.md")
        mock_filesystem.compute_checksum.return_value = "abc123"
        checksums = {str(file_path): "abc123"}
        errors: list[str] = []

        outcome, fragments = service._process_file(file_path, checksums, None, errors)

        assert outcome == "skipped"
        assert fragments == 0
        mock_chroma.add_fragments.assert_not_called()

    def should_remove_document_from_index(self, service, mock_chroma, mock_checksums):
        mock_checksums.load.return_value = {"/path/to/doc.md": "abc123"}
        saved_checksum_maps: list[dict] = []
        mock_checksums.save.side_effect = lambda cs: saved_checksum_maps.append(dict(cs))

        service.remove_document("/path/to/doc.md")

        assert len(saved_checksum_maps) == 1
        assert "/path/to/doc.md" not in saved_checksum_maps[0]

    def should_return_stats_with_no_checksums(self, service, mock_chroma, mock_checksums):
        mock_chroma.count.return_value = 0
        mock_checksums.load.return_value = {}
        mock_checksums.last_modified.return_value = None

        stats = service.get_stats()

        assert stats.repository_name == "test-repo"
        assert stats.total_documents == 0
        assert stats.total_fragments == 0
        assert stats.last_indexed is None

    def should_return_stats_with_existing_checksums(self, service, mock_chroma, mock_checksums):
        mock_chroma.count.return_value = 10
        mock_checksums.load.return_value = {"/doc1.md": "abc", "/doc2.md": "def"}
        mock_checksums.last_modified.return_value = datetime(2024, 1, 15, 10, 30)

        stats = service.get_stats()

        assert stats.total_documents == 2
        assert stats.total_fragments == 10
        assert stats.last_indexed is not None

    class DescribePurgeExcludedDocuments:
        @pytest.fixture
        def mock_chroma(self):
            return Mock(spec=ChromaGateway)

        @pytest.fixture
        def service(self, mock_chroma, mock_checksums):
            return IndexService(
                filesystem_gateway=Mock(spec=FilesystemGateway),
                docling_gateway=Mock(spec=DoclingGateway),
                embedding_gateway=Mock(spec=EmbeddingGateway),
                chroma_gateway=mock_chroma,
                repo_name="test-repo",
                checksum_gateway=mock_checksums,
            )

        def should_purge_documents_matching_exclude_patterns(self, service, mock_chroma, mock_checksums):
            mock_chroma.count.return_value = 1
            mock_chroma.get_metadata_batch.return_value = [{"document_path": "/tmp/docs/node_modules/dep.md"}]
            mock_checksums.load.return_value = {"/tmp/docs/node_modules/dep.md": "abc"}
            config = RepositoryConfig(name="test-repo", path="/tmp/docs", exclude_patterns=["node_modules"])
            deleted_docs: list[tuple] = []
            mock_chroma.delete_by_document.side_effect = lambda coll, path: deleted_docs.append((coll, path))

            service.purge_excluded_documents(config)

            assert deleted_docs == [("documents", "/tmp/docs/node_modules/dep.md")]

        def should_return_count_of_purged_documents(self, service, mock_chroma, mock_checksums):
            mock_chroma.count.return_value = 3
            mock_chroma.get_metadata_batch.return_value = [
                {"document_path": "/tmp/docs/node_modules/a.md"},
                {"document_path": "/tmp/docs/node_modules/b.md"},
                {"document_path": "/tmp/docs/readme.md"},
            ]
            mock_checksums.load.return_value = {
                "/tmp/docs/node_modules/a.md": "a",
                "/tmp/docs/node_modules/b.md": "b",
                "/tmp/docs/readme.md": "c",
            }
            config = RepositoryConfig(name="test-repo", path="/tmp/docs", exclude_patterns=["node_modules"])

            count = service.purge_excluded_documents(config)

            assert count == 2

        def should_return_zero_when_no_patterns(self, service, mock_chroma, mock_checksums):
            config = RepositoryConfig(name="test-repo", path="/tmp/docs", exclude_patterns=[])

            count = service.purge_excluded_documents(config)

            assert count == 0

        def should_skip_documents_not_under_repo_base(self, service, mock_chroma, mock_checksums):
            mock_chroma.count.return_value = 1
            mock_chroma.get_metadata_batch.return_value = [
                {"document_path": "/other/place/node_modules/file.md"},
            ]
            mock_checksums.load.return_value = {}
            config = RepositoryConfig(name="test-repo", path="/tmp/docs", exclude_patterns=["node_modules"])

            count = service.purge_excluded_documents(config)

            assert count == 0

        def should_not_purge_documents_that_do_not_match(self, service, mock_chroma, mock_checksums):
            mock_chroma.count.return_value = 2
            mock_chroma.get_metadata_batch.return_value = [
                {"document_path": "/tmp/docs/src/main.md"},
                {"document_path": "/tmp/docs/README.md"},
            ]
            mock_checksums.load.return_value = {
                "/tmp/docs/src/main.md": "a",
                "/tmp/docs/README.md": "b",
            }
            config = RepositoryConfig(name="test-repo", path="/tmp/docs", exclude_patterns=["node_modules"])

            count = service.purge_excluded_documents(config)

            assert count == 0

        def should_paginate_through_large_collections(self, service, mock_chroma, mock_checksums):
            mock_chroma.count.return_value = 1200
            # Simulate 1200 docs across 3 pages; none match node_modules
            batch_500 = [{"document_path": f"/tmp/docs/file{i}.md"} for i in range(500)]
            batch_200 = [{"document_path": f"/tmp/docs/file{i}.md"} for i in range(500, 700)]
            mock_chroma.get_metadata_batch.side_effect = [batch_500, batch_500, batch_200]
            mock_checksums.load.return_value = {}
            config = RepositoryConfig(name="test-repo", path="/tmp/docs", exclude_patterns=["node_modules"])

            count = service.purge_excluded_documents(config)

            # None of the 1200 docs match node_modules, proving all pages were scanned
            assert count == 0

    class DescribeWithoutDocling:
        """Tests for degraded mode when docling is unavailable."""

        @pytest.fixture
        def service(self, mock_filesystem, mock_embedding, mock_chroma, mock_checksums):
            return IndexService(
                filesystem_gateway=mock_filesystem,
                docling_gateway=None,
                embedding_gateway=mock_embedding,
                chroma_gateway=mock_chroma,
                repo_name="test-repo",
                checksum_gateway=mock_checksums,
            )

        def should_skip_pdf_when_docling_unavailable(
            self, service, mock_filesystem, mock_chroma, mock_checksums, repo_config
        ):
            file_path = Path("/tmp/docs/report.pdf")
            mock_filesystem.list_files.return_value = [file_path]
            mock_filesystem.compute_checksum.return_value = "checksum"
            mock_checksums.load.return_value = {}

            result = service.index_repository(repo_config)

            assert result.documents_skipped == 1
            assert result.documents_indexed == 0
            assert result.documents_failed == 0

        def should_index_markdown_when_docling_unavailable(
            self, service, mock_filesystem, mock_chroma, mock_checksums, repo_config
        ):
            file_path = Path("/tmp/docs/readme.md")
            mock_filesystem.list_files.return_value = [file_path]
            mock_filesystem.compute_checksum.return_value = "checksum"
            mock_filesystem.read_file.return_value = "# Hello\n\nWorld"
            mock_checksums.load.return_value = {}

            result = service.index_repository(repo_config)

            assert result.documents_indexed == 1
            assert result.documents_failed == 0

        def should_index_txt_when_docling_unavailable(
            self, service, mock_filesystem, mock_chroma, mock_checksums, repo_config
        ):
            file_path = Path("/tmp/docs/notes.txt")
            mock_filesystem.list_files.return_value = [file_path]
            mock_filesystem.compute_checksum.return_value = "checksum"
            mock_filesystem.read_file.return_value = "Some plain text"
            mock_checksums.load.return_value = {}

            result = service.index_repository(repo_config)

            assert result.documents_indexed == 1
