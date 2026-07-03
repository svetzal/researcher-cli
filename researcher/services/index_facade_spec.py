from contextlib import contextmanager
from unittest.mock import Mock

import pytest

from researcher.conftest import make_repo
from researcher.exceptions import StorageError
from researcher.models import IndexingResult
from researcher.service_factory import ServiceFactory
from researcher.services.index_facade import index_file_in_repo, index_repos, remove_from_repo, update_repo_with_purge
from researcher.services.index_service import IndexService


class DescribeIndexFileInRepo:
    @pytest.fixture
    def mock_factory(self):
        return Mock(spec=ServiceFactory)

    @pytest.fixture
    def mock_index_service(self):
        return Mock(spec=IndexService)

    def should_propagate_storage_error_from_index_file(self, mock_factory, mock_index_service):
        repo = make_repo("test-repo")
        mock_factory.repository_service.get_repository.return_value = repo
        mock_factory.index_service.return_value = mock_index_service
        mock_index_service.index_file.side_effect = StorageError("disk full")

        with pytest.raises(StorageError):
            index_file_in_repo(mock_factory, "test-repo", "/tmp/file.md")


class DescribeRemoveFromRepo:
    @pytest.fixture
    def mock_factory(self):
        return Mock(spec=ServiceFactory)

    @pytest.fixture
    def mock_index_service(self):
        return Mock(spec=IndexService)

    def should_propagate_storage_error_from_remove_document(self, mock_factory, mock_index_service):
        repo = make_repo("test-repo")
        mock_factory.repository_service.get_repository.return_value = repo
        mock_factory.index_service.return_value = mock_index_service
        mock_index_service.remove_document.side_effect = StorageError("write failed")

        with pytest.raises(StorageError):
            remove_from_repo(mock_factory, "test-repo", "doc.md")


class DescribeUpdateRepoWithPurge:
    @pytest.fixture
    def mock_factory(self):
        return Mock(spec=ServiceFactory)

    @pytest.fixture
    def mock_index_service(self):
        return Mock(spec=IndexService)

    def should_purge_when_patterns_added_and_no_purge_false(self, mock_factory, mock_index_service):
        repo = make_repo("test-repo")
        mock_factory.repository_service.update_repository.return_value = (repo, ["node_modules"])
        mock_factory.index_service.return_value = mock_index_service
        mock_index_service.purge_excluded_documents.return_value = 3

        outcome = update_repo_with_purge(mock_factory, "test-repo", None, ["node_modules"], no_purge=False)

        mock_index_service.purge_excluded_documents.assert_called_once_with(repo)
        assert outcome.purged == 3

    def should_not_purge_when_no_purge_true(self, mock_factory, mock_index_service):
        repo = make_repo("test-repo")
        mock_factory.repository_service.update_repository.return_value = (repo, ["node_modules"])
        mock_factory.index_service.return_value = mock_index_service

        outcome = update_repo_with_purge(mock_factory, "test-repo", None, ["node_modules"], no_purge=True)

        mock_index_service.purge_excluded_documents.assert_not_called()
        assert outcome.purged == 0

    def should_not_purge_when_no_patterns_added(self, mock_factory, mock_index_service):
        repo = make_repo("test-repo")
        mock_factory.repository_service.update_repository.return_value = (repo, [])
        mock_factory.index_service.return_value = mock_index_service

        outcome = update_repo_with_purge(mock_factory, "test-repo", None, [], no_purge=False)

        mock_index_service.purge_excluded_documents.assert_not_called()
        assert outcome.purged == 0


class DescribeIndexRepos:
    @pytest.fixture
    def mock_factory(self):
        return Mock(spec=ServiceFactory)

    @pytest.fixture
    def mock_index_service(self):
        return Mock(spec=IndexService)

    def should_call_index_repository_once_per_repo(self, mock_factory, mock_index_service):
        repo1 = make_repo("repo-a")
        repo2 = make_repo("repo-b")
        mock_factory.index_service.return_value = mock_index_service
        result_a = Mock(spec=IndexingResult)
        result_b = Mock(spec=IndexingResult)
        mock_index_service.index_repository.side_effect = [result_a, result_b]

        results = index_repos(mock_factory, [repo1, repo2], force=False)

        assert results == [("repo-a", result_a), ("repo-b", result_b)]
        assert mock_index_service.index_repository.call_count == 2

    def should_invoke_on_repo_context_manager_per_repo(self, mock_factory, mock_index_service):
        repo1 = make_repo("repo-a")
        mock_factory.index_service.return_value = mock_index_service
        mock_index_service.index_repository.return_value = Mock(spec=IndexingResult)

        entered = []

        @contextmanager
        def fake_on_repo(repo):
            entered.append(repo.name)
            yield

        index_repos(mock_factory, [repo1], force=False, on_repo=fake_on_repo)

        assert entered == ["repo-a"]

    def should_skip_on_repo_when_none(self, mock_factory, mock_index_service):
        repo1 = make_repo("repo-a")
        mock_factory.index_service.return_value = mock_index_service
        mock_index_service.index_repository.return_value = Mock(spec=IndexingResult)

        results = index_repos(mock_factory, [repo1], force=False, on_repo=None)

        assert len(results) == 1
        mock_index_service.index_repository.assert_called_once()
