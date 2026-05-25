import functools

import fastmcp

from researcher.exceptions import ResearcherError
from researcher.service_factory import ServiceFactory
from researcher.services.index_facade import get_repo_status, index_file_in_repo, remove_from_repo
from researcher.services.multi_repo_search import (
    search_documents_across_repos,
    search_fragments_across_repos,
)

mcp = fastmcp.FastMCP("researcher")


def _mcp_errors(on_error):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ResearcherError as e:
                return on_error(e)

        return wrapper

    return decorator


_factory: ServiceFactory | None = None


def _get_factory() -> ServiceFactory:
    global _factory
    if _factory is None:
        _factory = ServiceFactory()
    return _factory


def set_factory(factory: ServiceFactory) -> None:
    """Inject a factory — used by tests to avoid constructing a real ServiceFactory."""
    global _factory
    _factory = factory


@mcp.tool
@_mcp_errors(lambda e: f"Error: {e}")
def add_to_index(repository: str, file_path: str) -> str:
    """Index a specific file in a repository."""
    chunk_result = index_file_in_repo(_get_factory(), repository, file_path)
    count = len(chunk_result.fragments) if chunk_result else 0
    return f"Indexed {count} fragments from {file_path}"


@mcp.tool
@_mcp_errors(lambda e: f"Error: {e}")
def remove_from_index(repository: str, document_path: str) -> str:
    """Remove a document from a repository's index."""
    remove_from_repo(_get_factory(), repository, document_path)
    return f"Removed {document_path} from {repository}"


@mcp.tool
@_mcp_errors(lambda e: [{"error": str(e)}])
def search_fragments(query: str, repository: str | None = None, n_results: int = 10) -> list[dict]:
    """Search for text fragments across indexed repositories."""
    repos = _get_factory().repository_service.resolve_repos(repository)
    results = search_fragments_across_repos(_get_factory(), repos, query, n_results)
    return [r.model_dump() for r in results]


@mcp.tool
@_mcp_errors(lambda e: [{"error": str(e)}])
def search_documents(query: str, repository: str | None = None, n_results: int = 5) -> list[dict]:
    """Search for documents across indexed repositories, returning top fragments per document."""
    repos = _get_factory().repository_service.resolve_repos(repository)
    results = search_documents_across_repos(_get_factory(), repos, query, n_results)
    return [r.model_dump() for r in results]


@mcp.tool
@_mcp_errors(lambda e: [{"error": str(e)}])
def list_repositories() -> list[dict]:
    """List all configured repositories with their settings."""
    repos = _get_factory().repository_service.list_repositories()
    return [r.model_dump() for r in repos]


@mcp.tool
@_mcp_errors(lambda e: {"error": str(e)})
def get_index_status(repository: str | None = None) -> dict:
    """Get indexing statistics for one or all repositories."""
    statuses = [s.model_dump(mode="json") for s in get_repo_status(_get_factory(), repository)]
    if len(statuses) == 1:
        return statuses[0]
    return {"repositories": statuses}


def start_server(port: int | None = None) -> None:
    """Start the MCP server in HTTP or STDIO mode."""
    if port:
        mcp.run(transport="http", port=port)
    else:
        mcp.run()
