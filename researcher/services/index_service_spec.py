import json
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from researcher.config import RepositoryConfig
from researcher.gateways.chroma_gateway import ChromaGateway
from researcher.gateways.docling_gateway import DoclingGateway
from researcher.gateways.embedding_gateway import EmbeddingGateway
from researcher.gateways.filesystem_gateway import FilesystemGateway
from researcher.models import Fragment
from researcher.services.index_service import IndexService


class DescribeIndexService:
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

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
        return Mock(spec=ChromaGateway)

    @pytest.fixture
    def service(self, mock_filesystem, mock_docling, mock_embedding, mock_chroma, temp_dir):
        return IndexService(
            filesystem_gateway=mock_filesystem,
            docling_gateway=mock_docling,
            embedding_gateway=mock_embedding,
            chroma_gateway=mock_chroma,
            repo_name="test-repo",
            repo_data_dir=temp_dir,
        )

    @pytest.fixture
    def repo_config(self):
        return RepositoryConfig(name="test-repo", path="/tmp/docs", embedding_provider="chromadb")

    def should_skip_unchanged_files(self, service, mock_filesystem, mock_docling, mock_chroma, temp_dir, repo_config):
        file_path = Path("/tmp/docs/doc.md")
        mock_filesystem.list_files.return_value = [file_path]
        mock_filesystem.compute_checksum.return_value = "abc123"

        checksums_path = temp_dir / "checksums.json"
        checksums_path.write_text(json.dumps({str(file_path): "abc123"}))

        result = service.index_repository(repo_config)

        assert result.documents_skipped == 1
        assert result.documents_indexed == 0
        mock_docling.convert.assert_not_called()

    def should_pass_exclude_patterns_to_list_files(self, service, mock_filesystem, mock_docling, mock_chroma):
        repo_config = RepositoryConfig(
            name="test-repo",
            path="/tmp/docs",
            embedding_provider="chromadb",
            exclude_patterns=["node_modules", ".*"],
        )
        mock_filesystem.list_files.return_value = []

        service.index_repository(repo_config)

        mock_filesystem.list_files.assert_called_once_with(repo_config.file_types, ["node_modules", ".*"])

    def should_pass_empty_exclude_patterns_when_none_configured(
        self, service, mock_filesystem, mock_docling, mock_chroma, repo_config
    ):
        mock_filesystem.list_files.return_value = []

        service.index_repository(repo_config)

        mock_filesystem.list_files.assert_called_once_with(repo_config.file_types, [])

    def should_index_new_files(self, service, mock_filesystem, mock_docling, mock_chroma, repo_config):
        file_path = Path("/tmp/docs/doc.md")
        mock_filesystem.list_files.return_value = [file_path]
        mock_filesystem.compute_checksum.return_value = "new_checksum"
        mock_docling.convert.return_value = "mock_document"
        mock_docling.chunk.return_value = [Fragment(text="Hello world", document_path=str(file_path), fragment_index=0)]

        result = service.index_repository(repo_config)

        assert result.documents_indexed == 1
        assert result.fragments_created == 1
        mock_chroma.add_fragments.assert_called_once()

    def should_delete_old_fragments_before_reindexing(
        self, service, mock_filesystem, mock_docling, mock_chroma, temp_dir, repo_config
    ):
        file_path = Path("/tmp/docs/doc.md")
        mock_filesystem.list_files.return_value = [file_path]
        mock_filesystem.compute_checksum.return_value = "new_checksum"
        mock_docling.convert.return_value = "mock_document"
        mock_docling.chunk.return_value = [
            Fragment(text="Updated text", document_path=str(file_path), fragment_index=0)
        ]

        checksums_path = temp_dir / "checksums.json"
        checksums_path.write_text(json.dumps({str(file_path): "old_checksum"}))

        service.index_repository(repo_config)

        mock_chroma.delete_by_document.assert_called_once()

    def should_record_errors_without_reraise(self, service, mock_filesystem, mock_docling, mock_chroma, repo_config):
        file_path = Path("/tmp/docs/bad.md")
        mock_filesystem.list_files.return_value = [file_path]
        mock_filesystem.compute_checksum.return_value = "checksum"
        mock_docling.convert.side_effect = RuntimeError("Conversion failed")

        result = service.index_repository(repo_config)

        assert result.documents_failed == 1
        assert len(result.errors) == 1
        assert "Conversion failed" in result.errors[0]

    def should_use_external_embeddings_for_non_chromadb_provider(
        self, service, mock_filesystem, mock_docling, mock_embedding, mock_chroma, repo_config
    ):
        repo_config = RepositoryConfig(name="test-repo", path="/tmp/docs", embedding_provider="ollama")
        file_path = Path("/tmp/docs/doc.md")
        mock_filesystem.list_files.return_value = [file_path]
        mock_filesystem.compute_checksum.return_value = "checksum"
        mock_docling.convert.return_value = "mock_document"
        mock_docling.chunk.return_value = [Fragment(text="Hello world", document_path=str(file_path), fragment_index=0)]
        mock_embedding.embed_texts.return_value = [[0.1, 0.2, 0.3]]

        service.index_repository(repo_config)

        mock_embedding.embed_texts.assert_called_once_with(["Hello world"])
        mock_chroma.add_fragments_with_embeddings.assert_called_once()

    def should_remove_document_from_index(self, service, mock_chroma, temp_dir):
        checksums_path = temp_dir / "checksums.json"
        checksums_path.write_text(json.dumps({"/path/to/doc.md": "abc123"}))

        service.remove_document("/path/to/doc.md")

        mock_chroma.delete_by_document.assert_called_once()
        loaded = json.loads(checksums_path.read_text())
        assert "/path/to/doc.md" not in loaded

    def should_return_stats_with_no_checksums(self, service, mock_chroma):
        mock_chroma.count.return_value = 0

        stats = service.get_stats()

        assert stats.repository_name == "test-repo"
        assert stats.total_documents == 0
        assert stats.total_fragments == 0
        assert stats.last_indexed is None

    def should_return_stats_with_existing_checksums(self, service, mock_chroma, temp_dir):
        checksums_path = temp_dir / "checksums.json"
        checksums_path.write_text(json.dumps({"/doc1.md": "abc", "/doc2.md": "def"}))
        mock_chroma.count.return_value = 10

        stats = service.get_stats()

        assert stats.total_documents == 2
        assert stats.total_fragments == 10
        assert stats.last_indexed is not None

    class DescribePurgeExcludedDocuments:
        @pytest.fixture
        def temp_dir(self):
            with tempfile.TemporaryDirectory() as d:
                yield Path(d)

        @pytest.fixture
        def mock_chroma(self):
            return Mock(spec=ChromaGateway)

        @pytest.fixture
        def service(self, mock_chroma, temp_dir):
            return IndexService(
                filesystem_gateway=Mock(spec=FilesystemGateway),
                docling_gateway=Mock(spec=DoclingGateway),
                embedding_gateway=Mock(spec=EmbeddingGateway),
                chroma_gateway=mock_chroma,
                repo_name="test-repo",
                repo_data_dir=temp_dir,
            )

        def should_purge_documents_matching_exclude_patterns(self, service, mock_chroma, temp_dir):
            mock_chroma.get_all_document_paths.return_value = ["/tmp/docs/node_modules/dep.md"]
            checksums_path = temp_dir / "checksums.json"
            checksums_path.write_text(json.dumps({"/tmp/docs/node_modules/dep.md": "abc"}))
            config = RepositoryConfig(name="test-repo", path="/tmp/docs", exclude_patterns=["node_modules"])

            service.purge_excluded_documents(config)

            mock_chroma.delete_by_document.assert_called_once_with("documents", "/tmp/docs/node_modules/dep.md")

        def should_return_count_of_purged_documents(self, service, mock_chroma, temp_dir):
            mock_chroma.get_all_document_paths.return_value = [
                "/tmp/docs/node_modules/a.md",
                "/tmp/docs/node_modules/b.md",
                "/tmp/docs/readme.md",
            ]
            checksums_path = temp_dir / "checksums.json"
            checksums_path.write_text(
                json.dumps(
                    {
                        "/tmp/docs/node_modules/a.md": "a",
                        "/tmp/docs/node_modules/b.md": "b",
                        "/tmp/docs/readme.md": "c",
                    }
                )
            )
            config = RepositoryConfig(name="test-repo", path="/tmp/docs", exclude_patterns=["node_modules"])

            count = service.purge_excluded_documents(config)

            assert count == 2

        def should_return_zero_when_no_patterns(self, service, mock_chroma):
            config = RepositoryConfig(name="test-repo", path="/tmp/docs", exclude_patterns=[])

            count = service.purge_excluded_documents(config)

            assert count == 0
            mock_chroma.get_all_document_paths.assert_not_called()

        def should_skip_documents_not_under_repo_base(self, service, mock_chroma, temp_dir):
            mock_chroma.get_all_document_paths.return_value = [
                "/other/place/node_modules/file.md",
            ]
            checksums_path = temp_dir / "checksums.json"
            checksums_path.write_text(json.dumps({}))
            config = RepositoryConfig(name="test-repo", path="/tmp/docs", exclude_patterns=["node_modules"])

            count = service.purge_excluded_documents(config)

            assert count == 0
            mock_chroma.delete_by_document.assert_not_called()

        def should_not_purge_documents_that_do_not_match(self, service, mock_chroma, temp_dir):
            mock_chroma.get_all_document_paths.return_value = [
                "/tmp/docs/src/main.md",
                "/tmp/docs/README.md",
            ]
            checksums_path = temp_dir / "checksums.json"
            checksums_path.write_text(
                json.dumps(
                    {
                        "/tmp/docs/src/main.md": "a",
                        "/tmp/docs/README.md": "b",
                    }
                )
            )
            config = RepositoryConfig(name="test-repo", path="/tmp/docs", exclude_patterns=["node_modules"])

            count = service.purge_excluded_documents(config)

            assert count == 0
            mock_chroma.delete_by_document.assert_not_called()
