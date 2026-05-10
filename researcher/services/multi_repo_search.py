from collections.abc import Callable

import structlog

from researcher.config import RepositoryConfig
from researcher.exceptions import EmbeddingError, StorageError
from researcher.models import DocumentSearchResult, SearchResult
from researcher.service_factory import ServiceFactory

logger = structlog.get_logger()


def _search_across_repos[T](
    factory: ServiceFactory,
    repos: list[RepositoryConfig],
    query: str,
    n_results: int,
    search_method: Callable,
    sort_key: Callable[[T], float],
) -> list[T]:
    all_results: list[T] = []
    for repo in repos:
        service = factory.search_service(repo)
        try:
            all_results.extend(search_method(service, query, n_results=n_results))
        except (StorageError, EmbeddingError) as e:
            logger.warning("Search failed for repository", repo=repo.name, error=str(e))
    all_results.sort(key=sort_key)
    return all_results[:n_results]


def search_fragments_across_repos(
    factory: ServiceFactory,
    repos: list[RepositoryConfig],
    query: str,
    n_results: int,
) -> list[SearchResult]:
    """Search for fragments across multiple repositories, returning the top N globally by distance."""
    return _search_across_repos(
        factory,
        repos,
        query,
        n_results,
        lambda svc, q, **kw: svc.search_fragments(q, **kw),
        lambda r: r.distance,
    )


def search_documents_across_repos(
    factory: ServiceFactory,
    repos: list[RepositoryConfig],
    query: str,
    n_results: int,
) -> list[DocumentSearchResult]:
    """Search for documents across multiple repositories, returning the top N globally by best distance."""
    return _search_across_repos(
        factory,
        repos,
        query,
        n_results,
        lambda svc, q, **kw: svc.search_documents(q, **kw),
        lambda r: r.best_distance,
    )
