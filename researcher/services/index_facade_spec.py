from pathlib import Path
from unittest.mock import Mock

from researcher.models import ChunkResult, IndexStats
from researcher.service_factory import ServiceFactory
from researcher.services.index_facade import get_repo_status, index_file_in_repo, remove_from_repo


class DescribeIndexFileInRepo:
    def should_resolve_repo_and_index_file(self):
        factory = Mock(spec=ServiceFactory)
        mock_repo = Mock()
        factory.repository_service.get_repository.return_value = mock_repo
        mock_service = Mock()
        mock_result = Mock(spec=ChunkResult)
        mock_service.index_file.return_value = mock_result
        factory.index_service.return_value = mock_service

        result = index_file_in_repo(factory, "my-notes", "/path/to/file.md")

        factory.repository_service.get_repository.assert_called_once_with("my-notes")
        factory.index_service.assert_called_once_with(mock_repo)
        mock_service.index_file.assert_called_once_with(Path("/path/to/file.md"), mock_repo)
        assert result is mock_result

    def should_return_none_when_service_returns_none(self):
        factory = Mock(spec=ServiceFactory)
        mock_repo = Mock()
        factory.repository_service.get_repository.return_value = mock_repo
        mock_service = Mock()
        mock_service.index_file.return_value = None
        factory.index_service.return_value = mock_service

        result = index_file_in_repo(factory, "my-notes", "/path/to/file.md")

        assert result is None


class DescribeRemoveFromRepo:
    def should_resolve_repo_and_remove_document(self):
        factory = Mock(spec=ServiceFactory)
        mock_repo = Mock()
        factory.repository_service.get_repository.return_value = mock_repo
        mock_service = Mock()
        factory.index_service.return_value = mock_service

        remove_from_repo(factory, "my-notes", "some/doc.md")

        factory.repository_service.get_repository.assert_called_once_with("my-notes")
        factory.index_service.assert_called_once_with(mock_repo)
        mock_service.remove_document.assert_called_once_with("some/doc.md")


class DescribeGetRepoStatus:
    def should_return_stats_for_named_repo(self):
        factory = Mock(spec=ServiceFactory)
        mock_repo = Mock()
        factory.repository_service.get_repository.return_value = mock_repo
        mock_service = Mock()
        mock_stats = Mock(spec=IndexStats)
        mock_service.get_stats.return_value = mock_stats
        factory.index_service.return_value = mock_service

        result = get_repo_status(factory, "my-notes")

        factory.repository_service.get_repository.assert_called_once_with("my-notes")
        assert result == [mock_stats]

    def should_return_stats_for_all_repos_when_name_is_none(self):
        factory = Mock(spec=ServiceFactory)
        mock_repo1 = Mock()
        mock_repo2 = Mock()
        factory.repository_service.list_repositories.return_value = [mock_repo1, mock_repo2]
        mock_service = Mock()
        mock_stats = Mock(spec=IndexStats)
        mock_service.get_stats.return_value = mock_stats
        factory.index_service.return_value = mock_service

        result = get_repo_status(factory, None)

        factory.repository_service.list_repositories.assert_called_once()
        assert len(result) == 2

    def should_return_empty_list_when_no_repos_configured(self):
        factory = Mock(spec=ServiceFactory)
        factory.repository_service.list_repositories.return_value = []

        result = get_repo_status(factory, None)

        assert result == []
