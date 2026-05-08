from unittest.mock import Mock

import pytest

from researcher.conftest import make_repo
from researcher.exceptions import StorageError
from researcher.service_factory import ServiceFactory
from researcher.services.index_facade import index_file_in_repo, remove_from_repo
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
