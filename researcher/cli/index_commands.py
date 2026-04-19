from researcher.config import RepositoryConfig
from researcher.service_factory import ServiceFactory


def run_index(factory: ServiceFactory, repo: RepositoryConfig, *, force: bool = False) -> dict:
    """Index a single repository silently.

    Returns a dict describing the indexing result for the repository.
    """
    service = factory.index_service(repo)
    result = service.index_repository(repo, force=force)
    return {
        "repository": repo.name,
        "documents_indexed": result.documents_indexed,
        "documents_skipped": result.documents_skipped,
        "documents_failed": result.documents_failed,
        "documents_purged": result.documents_purged,
        "fragments_created": result.fragments_created,
        "errors": result.errors,
    }


def run_status(factory: ServiceFactory, repo: RepositoryConfig) -> dict:
    """Return index stats for a single repository."""
    service = factory.index_service(repo)
    stats = service.get_stats()
    return {
        "repository_name": stats.repository_name,
        "total_documents": stats.total_documents,
        "total_fragments": stats.total_fragments,
        "last_indexed": stats.last_indexed.isoformat() if stats.last_indexed else None,
    }


def build_json_results_wrapper(results: list[dict]) -> dict:
    """Build the JSON-serializable wrapper dict for multi-repo results."""
    return {"repositories": results}
