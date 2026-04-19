from datetime import datetime
from unittest.mock import Mock

from researcher.cli.index_commands import build_json_results_wrapper, run_index, run_status
from researcher.config import RepositoryConfig
from researcher.models import IndexingResult, IndexStats
from researcher.service_factory import ServiceFactory
from researcher.services.index_service import IndexService


def _make_repo(name: str = "my-notes") -> RepositoryConfig:
    return RepositoryConfig(name=name, path="/tmp/notes")


def _make_indexing_result(
    documents_indexed: int = 5,
    documents_skipped: int = 37,
    documents_failed: int = 0,
    documents_purged: int = 0,
    fragments_created: int = 50,
    errors: list[str] | None = None,
) -> IndexingResult:
    return IndexingResult(
        documents_indexed=documents_indexed,
        documents_skipped=documents_skipped,
        documents_failed=documents_failed,
        documents_purged=documents_purged,
        fragments_created=fragments_created,
        errors=errors or [],
    )


def _make_index_stats(
    repository_name: str = "my-notes",
    total_documents: int = 42,
    total_fragments: int = 318,
    last_indexed: datetime | None = None,
) -> IndexStats:
    return IndexStats(
        repository_name=repository_name,
        total_documents=total_documents,
        total_fragments=total_fragments,
        last_indexed=last_indexed,
    )


class DescribeRunIndex:
    def should_return_dict_with_correct_fields(self):
        repo = _make_repo()
        mock_factory = Mock(spec=ServiceFactory)
        mock_index = Mock(spec=IndexService)
        mock_index.index_repository.return_value = _make_indexing_result()
        mock_factory.index_service.return_value = mock_index

        result = run_index(mock_factory, repo)

        assert result["repository"] == "my-notes"
        assert result["documents_indexed"] == 5
        assert result["documents_skipped"] == 37
        assert result["documents_failed"] == 0
        assert result["fragments_created"] == 50
        assert result["errors"] == []

    def should_include_errors_in_result(self):
        repo = _make_repo()
        mock_factory = Mock(spec=ServiceFactory)
        mock_index = Mock(spec=IndexService)
        mock_index.index_repository.return_value = _make_indexing_result(
            documents_failed=1, errors=["Failed to parse file.md"]
        )
        mock_factory.index_service.return_value = mock_index

        result = run_index(mock_factory, repo)

        assert result["documents_failed"] == 1
        assert "Failed to parse file.md" in result["errors"]


class DescribeRunStatus:
    def should_return_dict_with_correct_fields(self):
        repo = _make_repo()
        mock_factory = Mock(spec=ServiceFactory)
        mock_index = Mock(spec=IndexService)
        mock_index.get_stats.return_value = _make_index_stats()
        mock_factory.index_service.return_value = mock_index

        result = run_status(mock_factory, repo)

        assert result["repository_name"] == "my-notes"
        assert result["total_documents"] == 42
        assert result["total_fragments"] == 318
        assert result["last_indexed"] is None

    def should_serialize_last_indexed_as_iso_string(self):
        repo = _make_repo()
        ts = datetime(2026, 2, 20, 10, 0, 0)
        mock_factory = Mock(spec=ServiceFactory)
        mock_index = Mock(spec=IndexService)
        mock_index.get_stats.return_value = _make_index_stats(last_indexed=ts)
        mock_factory.index_service.return_value = mock_index

        result = run_status(mock_factory, repo)

        assert result["last_indexed"] == "2026-02-20T10:00:00"


class DescribeBuildJsonResultsWrapper:
    def should_wrap_results_in_repositories_key(self):
        results = [
            {
                "repository": "my-notes",
                "documents_indexed": 5,
                "documents_skipped": 37,
                "documents_failed": 0,
                "fragments_created": 50,
                "errors": [],
            }
        ]

        data = build_json_results_wrapper(results)

        assert "repositories" in data
        assert len(data["repositories"]) == 1
        assert data["repositories"][0]["repository"] == "my-notes"

    def should_wrap_status_results_the_same_way(self):
        results = [
            {
                "repository_name": "my-notes",
                "total_documents": 42,
                "total_fragments": 318,
                "last_indexed": None,
            }
        ]

        data = build_json_results_wrapper(results)

        assert "repositories" in data
        assert data["repositories"][0]["repository_name"] == "my-notes"
