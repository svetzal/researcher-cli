from pathlib import Path
from typing import Optional

import fastmcp

from researcher.service_factory import ServiceFactory

mcp = fastmcp.FastMCP("researcher")
_factory = ServiceFactory()


@mcp.tool
def add_to_index(repository: str, file_path: str) -> str:
    """Index a specific file in a repository."""
    repo = _factory.repository_service.get_repository(repository)
    service = _factory.index_service(repo)
    chunk_result = service.index_file(Path(file_path), repo)
    return f"Indexed {len(chunk_result.fragments)} fragments from {file_path}"


@mcp.tool
def remove_from_index(repository: str, document_path: str) -> str:
    """Remove a document from a repository's index."""
    repo = _factory.repository_service.get_repository(repository)
    service = _factory.index_service(repo)
    service.remove_document(document_path)
    return f"Removed {document_path} from {repository}"


@mcp.tool
def search_fragments(query: str, repository: Optional[str] = None, n_results: int = 10) -> list[dict]:
    """Search for text fragments across indexed repositories."""
    repos = _get_repos(repository)
    all_results = []
    for repo in repos:
        service = _factory.search_service(repo)
        results = service.search_fragments(query, n_results=n_results)
        all_results.extend(r.model_dump() for r in results)

    all_results.sort(key=lambda r: r["distance"])
    return all_results[:n_results]


@mcp.tool
def search_documents(query: str, repository: Optional[str] = None, n_results: int = 5) -> list[dict]:
    """Search for documents across indexed repositories, returning top fragments per document."""
    repos = _get_repos(repository)
    all_results = []
    for repo in repos:
        service = _factory.search_service(repo)
        results = service.search_documents(query, n_results=n_results)
        all_results.extend(r.model_dump() for r in results)

    all_results.sort(key=lambda r: r["best_distance"])
    return all_results[:n_results]


@mcp.tool
def list_repositories() -> list[dict]:
    """List all configured repositories with their settings."""
    repos = _factory.repository_service.list_repositories()
    return [r.model_dump() for r in repos]


@mcp.tool
def get_index_status(repository: Optional[str] = None) -> dict:
    """Get indexing statistics for one or all repositories."""
    repos = _get_repos(repository)
    statuses = []
    for repo in repos:
        service = _factory.index_service(repo)
        stats = service.get_stats()
        statuses.append(stats.model_dump(mode="json"))

    if len(statuses) == 1:
        return statuses[0]
    return {"repositories": statuses}


def _get_repos(repository: Optional[str]):
    """Return a list of repos — one if named, all if None."""
    if repository:
        return [_factory.repository_service.get_repository(repository)]
    return _factory.repository_service.list_repositories()


def start_server(port: Optional[int] = None) -> None:
    """Start the MCP server in HTTP or STDIO mode."""
    if port:
        mcp.run(transport="http", port=port)
    else:
        mcp.run()
