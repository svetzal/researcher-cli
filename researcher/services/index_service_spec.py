from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

from researcher.config import RepositoryConfig
from researcher.gateways.checksum_gateway import ChecksumGateway
from researcher.gateways.chroma_gateway import ChromaGateway
from researcher.gateways.docling_gateway import DoclingGateway
from researcher.gateways.embedding_gateway import EmbeddingGateway
from researcher.gateways.filesystem_gateway import FilesystemGateway
from researcher.models import Fragment
from researcher.services.index_service import IndexService


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
        m.get_all_document_paths.return_value = []
        return m

    @pytest.fixture
    def mock_checksums(self):
        return Mock(spec=ChecksumGateway)

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
        mock_docling.convert.assert_not_called()

    def should_pass_exclude_patterns_to_list_files(
        self, service, mock_filesystem, mock_docling, mock_chroma, mock_checksums
    ):
        repo_config = RepositoryConfig(
            name="test-repo",
            path="/tmp/docs",
            embedding_provider="chromadb",
            exclude_patterns=["node_modules", ".*"],
        )
        mock_filesystem.list_files.return_value = []
        mock_chroma.get_all_document_paths.return_value = []
        mock_checksums.load.return_value = {}

        service.index_repository(repo_config)

        mock_filesystem.list_files.assert_called_once_with(repo_config.file_types, ["node_modules", ".*"])

    def should_pass_default_exclude_patterns_to_list_files(
        self, service, mock_filesystem, mock_docling, mock_chroma, mock_checksums, repo_config
    ):
        mock_filesystem.list_files.return_value = []
        mock_checksums.load.return_value = {}

        service.index_repository(repo_config)

        mock_filesystem.list_files.assert_called_once_with(repo_config.file_types, [".*"])

    def should_index_new_files(self, service, mock_filesystem, mock_docling, mock_chroma, mock_checksums, repo_config):
        file_path = Path("/tmp/docs/doc.pdf")
        mock_filesystem.list_files.return_value = [file_path]
        mock_filesystem.compute_checksum.return_value = "new_checksum"
        mock_docling.convert.return_value = "mock_document"
        mock_docling.chunk.return_value = [Fragment(text="Hello world", document_path=str(file_path), fragment_index=0)]
        mock_checksums.load.return_value = {}

        result = service.index_repository(repo_config)

        assert result.documents_indexed == 1
        assert result.fragments_created == 1
        mock_chroma.add_fragments.assert_called_once()

    def should_delete_old_fragments_before_reindexing(
        self, service, mock_filesystem, mock_docling, mock_chroma, mock_checksums, repo_config
    ):
        file_path = Path("/tmp/docs/doc.pdf")
        mock_filesystem.list_files.return_value = [file_path]
        mock_filesystem.compute_checksum.return_value = "new_checksum"
        mock_docling.convert.return_value = "mock_document"
        mock_docling.chunk.return_value = [
            Fragment(text="Updated text", document_path=str(file_path), fragment_index=0)
        ]
        mock_checksums.load.return_value = {str(file_path): "old_checksum"}

        service.index_repository(repo_config)

        mock_chroma.delete_by_document.assert_called_once()

    def should_bypass_docling_for_plain_text_files(
        self, service, mock_filesystem, mock_docling, mock_chroma, mock_checksums, repo_config
    ):
        file_path = Path("/tmp/docs/notes.txt")
        mock_filesystem.list_files.return_value = [file_path]
        mock_filesystem.compute_checksum.return_value = "new_checksum"
        mock_filesystem.read_file.return_value = "Some plain text content"
        mock_checksums.load.return_value = {}

        result = service.index_repository(repo_config)

        assert result.documents_indexed == 1
        mock_docling.convert.assert_not_called()
        mock_docling.chunk.assert_not_called()
        mock_filesystem.read_file.assert_called_once_with(file_path)

    def should_bypass_docling_for_markdown_files(
        self, service, mock_filesystem, mock_docling, mock_chroma, mock_checksums, repo_config
    ):
        file_path = Path("/tmp/docs/readme.md")
        mock_filesystem.list_files.return_value = [file_path]
        mock_filesystem.compute_checksum.return_value = "new_checksum"
        mock_filesystem.read_file.return_value = "# Heading\n\nSome markdown content"
        mock_checksums.load.return_value = {}

        result = service.index_repository(repo_config)

        assert result.documents_indexed == 1
        mock_docling.convert.assert_not_called()
        mock_docling.chunk.assert_not_called()

    def should_use_docling_for_pdf_files(
        self, service, mock_filesystem, mock_docling, mock_chroma, mock_checksums, repo_config
    ):
        file_path = Path("/tmp/docs/report.pdf")
        mock_filesystem.list_files.return_value = [file_path]
        mock_filesystem.compute_checksum.return_value = "new_checksum"
        mock_docling.convert.return_value = "mock_document"
        mock_docling.chunk.return_value = [Fragment(text="PDF content", document_path=str(file_path), fragment_index=0)]
        mock_checksums.load.return_value = {}

        result = service.index_repository(repo_config)

        assert result.documents_indexed == 1
        mock_docling.convert.assert_called_once_with(file_path)
        mock_filesystem.read_file.assert_not_called()

    def should_record_errors_without_reraise(
        self, service, mock_filesystem, mock_docling, mock_chroma, mock_checksums, repo_config
    ):
        file_path = Path("/tmp/docs/bad.pdf")
        mock_filesystem.list_files.return_value = [file_path]
        mock_filesystem.compute_checksum.return_value = "checksum"
        mock_docling.convert.side_effect = RuntimeError("Conversion failed")
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
        mock_docling.chunk.return_value = [Fragment(text="Hello world", document_path=str(file_path), fragment_index=0)]
        mock_embedding.embed_texts.return_value = [[0.1, 0.2, 0.3]]
        mock_checksums.load.return_value = {}

        service.index_repository(repo_config)

        mock_embedding.embed_texts.assert_called_once_with(["Hello world"])
        mock_chroma.add_fragments_with_embeddings.assert_called_once()

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
        mock_chroma.get_all_document_paths.return_value = [
            "/tmp/docs/readme.md",
            "/tmp/docs/node_modules/dep.md",
        ]
        mock_filesystem.list_files.return_value = [Path("/tmp/docs/readme.md")]
        mock_filesystem.compute_checksum.return_value = "aaa"

        result = service.index_repository(repo_config)

        assert result.documents_purged == 1
        mock_chroma.delete_by_document.assert_called_once_with("documents", "/tmp/docs/node_modules/dep.md")
        # The purged document should be removed from the saved checksums
        saved_checksums = mock_checksums.save.call_args[0][0]
        assert "/tmp/docs/node_modules/dep.md" not in saved_checksums

    def should_remove_document_from_index(self, service, mock_chroma, mock_checksums):
        mock_checksums.load.return_value = {"/path/to/doc.md": "abc123"}

        service.remove_document("/path/to/doc.md")

        mock_chroma.delete_by_document.assert_called_once()
        saved_checksums = mock_checksums.save.call_args[0][0]
        assert "/path/to/doc.md" not in saved_checksums

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
        def mock_checksums(self):
            return Mock(spec=ChecksumGateway)

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
            mock_chroma.get_all_document_paths.return_value = ["/tmp/docs/node_modules/dep.md"]
            mock_checksums.load.return_value = {"/tmp/docs/node_modules/dep.md": "abc"}
            config = RepositoryConfig(name="test-repo", path="/tmp/docs", exclude_patterns=["node_modules"])

            service.purge_excluded_documents(config)

            mock_chroma.delete_by_document.assert_called_once_with("documents", "/tmp/docs/node_modules/dep.md")

        def should_return_count_of_purged_documents(self, service, mock_chroma, mock_checksums):
            mock_chroma.get_all_document_paths.return_value = [
                "/tmp/docs/node_modules/a.md",
                "/tmp/docs/node_modules/b.md",
                "/tmp/docs/readme.md",
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
            mock_chroma.get_all_document_paths.assert_not_called()

        def should_skip_documents_not_under_repo_base(self, service, mock_chroma, mock_checksums):
            mock_chroma.get_all_document_paths.return_value = [
                "/other/place/node_modules/file.md",
            ]
            mock_checksums.load.return_value = {}
            config = RepositoryConfig(name="test-repo", path="/tmp/docs", exclude_patterns=["node_modules"])

            count = service.purge_excluded_documents(config)

            assert count == 0
            mock_chroma.delete_by_document.assert_not_called()

        def should_not_purge_documents_that_do_not_match(self, service, mock_chroma, mock_checksums):
            mock_chroma.get_all_document_paths.return_value = [
                "/tmp/docs/src/main.md",
                "/tmp/docs/README.md",
            ]
            mock_checksums.load.return_value = {
                "/tmp/docs/src/main.md": "a",
                "/tmp/docs/README.md": "b",
            }
            config = RepositoryConfig(name="test-repo", path="/tmp/docs", exclude_patterns=["node_modules"])

            count = service.purge_excluded_documents(config)

            assert count == 0
            mock_chroma.delete_by_document.assert_not_called()
