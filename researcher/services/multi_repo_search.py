import structlog

from researcher.config import RepositoryConfig
from researcher.exceptions import EmbeddingError, StorageError
from researcher.models import DocumentSearchResult, SearchResult
from researcher.service_factory import ServiceFactory

logger = structlog.get_logger()


def search_fragments_across_repos(
    factory: ServiceFactory,
    repos: list[RepositoryConfig],
    query: str,
    n_results: int,
) -> list[SearchResult]:
    """Search for fragments across multiple repositories, returning the top N globally by distance."""
    all_results: list[SearchResult] = []
    for repo in repos:
        service = factory.search_service(repo)
        try:
            all_results.extend(service.search_fragments(query, n_results=n_results))
        except (StorageError, EmbeddingError) as e:
            logger.warning("Search failed for repository", repo=repo.name, error=str(e))
            continue

    all_results.sort(key=lambda r: r.distance)
    return all_results[:n_results]


def search_documents_across_repos(
    factory: ServiceFactory,
    repos: list[RepositoryConfig],
    query: str,
    n_results: int,
) -> list[DocumentSearchResult]:
    """Search for documents across multiple repositories, returning the top N globally by best distance."""
    all_results: list[DocumentSearchResult] = []
    for repo in repos:
        service = factory.search_service(repo)
        try:
            all_results.extend(service.search_documents(query, n_results=n_results))
        except (StorageError, EmbeddingError) as e:
            logger.warning("Search failed for repository", repo=repo.name, error=str(e))
            continue

    all_results.sort(key=lambda r: r.best_distance)
    return all_results[:n_results]
