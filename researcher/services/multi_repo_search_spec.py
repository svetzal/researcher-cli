from unittest.mock import Mock

import pytest

from researcher.conftest import make_doc_result, make_repo, make_search_result
from researcher.enums import SearchMode
from researcher.exceptions import EmbeddingError, StorageError
from researcher.service_factory import ServiceFactory
from researcher.services.multi_repo_search import search_across_repos
from researcher.services.search_service import SearchService


class DescribeSearchAcrossReposFragments:
    @pytest.fixture
    def mock_factory(self):
        return Mock(spec=ServiceFactory)

    @pytest.fixture
    def mock_search_service(self):
        return Mock(spec=SearchService)

    def should_return_fragments_from_single_repo(self, mock_factory, mock_search_service):
        repo = make_repo("repo-a")
        mock_factory.search_service.return_value = mock_search_service
        mock_search_service.search_fragments.return_value = [make_search_result("f1", distance=0.2)]

        outcome = search_across_repos(mock_factory, [repo], "query", n_results=5, mode=SearchMode.FRAGMENTS)

        assert len(outcome.results) == 1
        assert outcome.results[0].fragment_id == "f1"
        assert outcome.failed_repositories == []

    def should_merge_and_sort_fragments_from_multiple_repos(self, mock_factory, mock_search_service):
        repo_a = make_repo("repo-a")
        repo_b = make_repo("repo-b")
        near = make_search_result("near", distance=0.1)
        far = make_search_result("far", distance=0.9)
        mock_search_service_b = Mock(spec=SearchService)
        mock_factory.search_service.side_effect = [mock_search_service, mock_search_service_b]
        mock_search_service.search_fragments.return_value = [far]
        mock_search_service_b.search_fragments.return_value = [near]

        outcome = search_across_repos(mock_factory, [repo_a, repo_b], "query", n_results=5, mode=SearchMode.FRAGMENTS)

        assert len(outcome.results) == 2
        assert outcome.results[0].fragment_id == "near"
        assert outcome.results[1].fragment_id == "far"

    def should_truncate_to_n_results(self, mock_factory, mock_search_service):
        repo = make_repo()
        mock_factory.search_service.return_value = mock_search_service
        mock_search_service.search_fragments.return_value = [
            make_search_result(f"f{i}", distance=float(i)) for i in range(10)
        ]

        outcome = search_across_repos(mock_factory, [repo], "query", n_results=3, mode=SearchMode.FRAGMENTS)

        assert len(outcome.results) == 3

    def should_return_empty_list_when_no_repos(self, mock_factory):
        outcome = search_across_repos(mock_factory, [], "query", n_results=5, mode=SearchMode.FRAGMENTS)

        assert outcome.results == []
        assert outcome.failed_repositories == []

    def should_return_empty_list_when_repos_have_no_results(self, mock_factory, mock_search_service):
        repo = make_repo()
        mock_factory.search_service.return_value = mock_search_service
        mock_search_service.search_fragments.return_value = []

        outcome = search_across_repos(mock_factory, [repo], "query", n_results=5, mode=SearchMode.FRAGMENTS)

        assert outcome.results == []

    def should_return_results_from_healthy_repo_when_first_raises_embedding_error(
        self, mock_factory, mock_search_service
    ):
        repo_a = make_repo("bad-repo")
        repo_b = make_repo("good-repo")
        mock_search_service_b = Mock(spec=SearchService)
        mock_factory.search_service.side_effect = [mock_search_service, mock_search_service_b]
        mock_search_service.search_fragments.side_effect = EmbeddingError("provider down")
        mock_search_service_b.search_fragments.return_value = [make_search_result("f1", distance=0.1)]

        outcome = search_across_repos(mock_factory, [repo_a, repo_b], "query", n_results=5, mode=SearchMode.FRAGMENTS)

        assert len(outcome.results) == 1
        assert outcome.results[0].fragment_id == "f1"
        assert outcome.failed_repositories == ["bad-repo"]

    def should_raise_when_every_repository_fails(self, mock_factory, mock_search_service):
        repo_a = make_repo("bad-a")
        repo_b = make_repo("bad-b")
        mock_search_service_b = Mock(spec=SearchService)
        mock_factory.search_service.side_effect = [mock_search_service, mock_search_service_b]
        mock_search_service.search_fragments.side_effect = StorageError("disk full")
        mock_search_service_b.search_fragments.side_effect = StorageError("disk full")

        with pytest.raises(StorageError, match="disk full"):
            search_across_repos(mock_factory, [repo_a, repo_b], "query", n_results=5, mode=SearchMode.FRAGMENTS)

    def should_raise_when_single_repository_fails(self, mock_factory, mock_search_service):
        repo = make_repo("failing-repo")
        mock_factory.search_service.return_value = mock_search_service
        mock_search_service.search_fragments.side_effect = StorageError("chroma down")

        with pytest.raises(StorageError, match="chroma down"):
            search_across_repos(mock_factory, [repo], "query", n_results=5, mode=SearchMode.FRAGMENTS)


class DescribeSearchAcrossReposDocuments:
    @pytest.fixture
    def mock_factory(self):
        return Mock(spec=ServiceFactory)

    @pytest.fixture
    def mock_search_service(self):
        return Mock(spec=SearchService)

    def should_return_documents_from_single_repo(self, mock_factory, mock_search_service):
        repo = make_repo("repo-a")
        mock_factory.search_service.return_value = mock_search_service
        mock_search_service.search_documents.return_value = [make_doc_result("doc.md", best_distance=0.2)]

        outcome = search_across_repos(mock_factory, [repo], "query", n_results=5, mode=SearchMode.DOCUMENTS)

        assert len(outcome.results) == 1
        assert outcome.results[0].document_path == "doc.md"
        assert outcome.failed_repositories == []

    def should_merge_and_sort_documents_from_multiple_repos(self, mock_factory, mock_search_service):
        repo_a = make_repo("repo-a")
        repo_b = make_repo("repo-b")
        near = make_doc_result("near.md", best_distance=0.1)
        far = make_doc_result("far.md", best_distance=0.9)
        mock_search_service_b = Mock(spec=SearchService)
        mock_factory.search_service.side_effect = [mock_search_service, mock_search_service_b]
        mock_search_service.search_documents.return_value = [far]
        mock_search_service_b.search_documents.return_value = [near]

        outcome = search_across_repos(mock_factory, [repo_a, repo_b], "query", n_results=5, mode=SearchMode.DOCUMENTS)

        assert len(outcome.results) == 2
        assert outcome.results[0].document_path == "near.md"
        assert outcome.results[1].document_path == "far.md"

    def should_truncate_to_n_results(self, mock_factory, mock_search_service):
        repo = make_repo()
        mock_factory.search_service.return_value = mock_search_service
        mock_search_service.search_documents.return_value = [
            make_doc_result(f"doc{i}.md", best_distance=float(i)) for i in range(10)
        ]

        outcome = search_across_repos(mock_factory, [repo], "query", n_results=3, mode=SearchMode.DOCUMENTS)

        assert len(outcome.results) == 3

    def should_return_empty_list_when_no_repos(self, mock_factory):
        outcome = search_across_repos(mock_factory, [], "query", n_results=5, mode=SearchMode.DOCUMENTS)

        assert outcome.results == []
        assert outcome.failed_repositories == []

    def should_return_results_from_healthy_repo_when_first_raises_embedding_error(
        self, mock_factory, mock_search_service
    ):
        repo_a = make_repo("bad-repo")
        repo_b = make_repo("good-repo")
        mock_search_service_b = Mock(spec=SearchService)
        mock_factory.search_service.side_effect = [mock_search_service, mock_search_service_b]
        mock_search_service.search_documents.side_effect = EmbeddingError("provider down")
        mock_search_service_b.search_documents.return_value = [make_doc_result("doc.md", best_distance=0.1)]

        outcome = search_across_repos(mock_factory, [repo_a, repo_b], "query", n_results=5, mode=SearchMode.DOCUMENTS)

        assert len(outcome.results) == 1
        assert outcome.results[0].document_path == "doc.md"
        assert outcome.failed_repositories == ["bad-repo"]

    def should_raise_when_every_repository_fails(self, mock_factory, mock_search_service):
        repo_a = make_repo("bad-a")
        repo_b = make_repo("bad-b")
        mock_search_service_b = Mock(spec=SearchService)
        mock_factory.search_service.side_effect = [mock_search_service, mock_search_service_b]
        mock_search_service.search_documents.side_effect = StorageError("disk full")
        mock_search_service_b.search_documents.side_effect = StorageError("disk full")

        with pytest.raises(StorageError, match="disk full"):
            search_across_repos(mock_factory, [repo_a, repo_b], "query", n_results=5, mode=SearchMode.DOCUMENTS)

    def should_raise_when_single_repository_fails(self, mock_factory, mock_search_service):
        repo = make_repo("failing-repo")
        mock_factory.search_service.return_value = mock_search_service
        mock_search_service.search_documents.side_effect = StorageError("chroma down")

        with pytest.raises(StorageError, match="chroma down"):
            search_across_repos(mock_factory, [repo], "query", n_results=5, mode=SearchMode.DOCUMENTS)
