from typing import NoReturn

import fastmcp
from fastmcp.exceptions import ToolError

from researcher.cli.payloads import IndexStatusWrapper
from researcher.config import RepositoryConfig
from researcher.error_boundary import handle_boundary_errors
from researcher.exceptions import ResearcherError
from researcher.models import DocumentSearchResult, SearchResult
from researcher.service_factory import ServiceFactory
from researcher.services.index_facade import get_repo_status, index_and_store_file_in_repo, remove_from_repo
from researcher.services.multi_repo_search import (
    search_documents_across_repos,
    search_fragments_across_repos,
)


def _raise_tool_error(e: ResearcherError, **_: object) -> NoReturn:
    raise ToolError(str(e)) from e


_mcp_errors = handle_boundary_errors(ResearcherError, on_error=_raise_tool_error)


class ResearcherTools:
    def __init__(self, factory: ServiceFactory) -> None:
        self._factory = factory

    @_mcp_errors
    def add_to_index(self, repository: str, file_path: str) -> str:
        chunk_result = index_and_store_file_in_repo(self._factory, repository, file_path)
        count = len(chunk_result.fragments) if chunk_result else 0
        return f"Indexed {count} fragments from {file_path}"

    @_mcp_errors
    def remove_from_index(self, repository: str, document_path: str) -> str:
        remove_from_repo(self._factory, repository, document_path)
        return f"Removed {document_path} from {repository}"

    @_mcp_errors
    def search_fragments(self, query: str, repository: str | None = None, n_results: int = 10) -> list[SearchResult]:
        repos = self._factory.repository_service.resolve_repos(repository)
        return search_fragments_across_repos(self._factory, repos, query, n_results).results

    @_mcp_errors
    def search_documents(
        self, query: str, repository: str | None = None, n_results: int = 5
    ) -> list[DocumentSearchResult]:
        repos = self._factory.repository_service.resolve_repos(repository)
        return search_documents_across_repos(self._factory, repos, query, n_results).results

    @_mcp_errors
    def list_repositories(self) -> list[RepositoryConfig]:
        return self._factory.repository_service.list_repositories()

    @_mcp_errors
    def get_index_status(self, repository: str | None = None) -> dict[str, object] | IndexStatusWrapper:
        statuses = [s.model_dump(mode="json") for s in get_repo_status(self._factory, repository)]
        if len(statuses) == 1:
            return statuses[0]
        return {"repositories": statuses}


def build_server(factory: ServiceFactory) -> fastmcp.FastMCP:
    mcp = fastmcp.FastMCP("researcher")
    tools = ResearcherTools(factory)
    mcp.tool(tools.add_to_index)
    mcp.tool(tools.remove_from_index)
    mcp.tool(tools.search_fragments)
    mcp.tool(tools.search_documents)
    mcp.tool(tools.list_repositories)
    mcp.tool(tools.get_index_status)
    return mcp


def start_server(port: int | None = None) -> None:
    mcp = build_server(ServiceFactory())
    if port:
        mcp.run(transport="http", port=port)
    else:
        mcp.run()
