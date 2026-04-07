from rich.console import Console
from rich.panel import Panel

from researcher.cli.output import cli_output
from researcher.config import RepositoryConfig
from researcher.models import DocumentSearchResult, SearchResult
from researcher.service_factory import ServiceFactory
from researcher.services.multi_repo_search import (
    search_documents_across_repos,
    search_fragments_across_repos,
)

console = Console()


def build_fragment_search_result(
    repos: list[RepositoryConfig],
    query: str,
    results: list[SearchResult],
) -> dict:
    """Build the JSON-serializable result dict for a fragment search."""
    return {
        "query": query,
        "mode": "fragments",
        "repository": repos[0].name if len(repos) == 1 else None,
        "repos_searched": [r.name for r in repos],
        "result_count": len(results),
        "results": [
            {
                "document_path": r.document_path,
                "fragment_index": r.fragment_index,
                "distance": r.distance,
                "text": r.text,
            }
            for r in results
        ],
    }


def build_document_search_result(
    repos: list[RepositoryConfig],
    query: str,
    results: list[DocumentSearchResult],
) -> dict:
    """Build the JSON-serializable result dict for a document search."""
    results_data = []
    for doc_result in results:
        top = doc_result.top_fragments[0] if doc_result.top_fragments else None
        results_data.append(
            {
                "document_path": doc_result.document_path,
                "best_distance": doc_result.best_distance,
                "fragment_count": len(doc_result.top_fragments),
                "top_fragment": {
                    "text": top.text,
                    "fragment_index": top.fragment_index,
                    "distance": top.distance,
                }
                if top
                else None,
            }
        )
    return {
        "query": query,
        "mode": "documents",
        "repository": repos[0].name if len(repos) == 1 else None,
        "repos_searched": [r.name for r in repos],
        "result_count": len(results),
        "results": results_data,
    }


def run_search_fragments(
    factory: ServiceFactory,
    repos: list[RepositoryConfig],
    query: str,
    n_results: int,
    json_output: bool = False,
) -> None:
    """Search for fragments across one or more repositories."""
    all_results = search_fragments_across_repos(factory, repos, query, n_results)

    def _print_fragments():
        if not all_results:
            console.print("[dim]No results found.[/dim]")
            return
        for result in all_results:
            console.print(
                Panel(
                    result.text,
                    title=f"[bold]{result.document_path}[/bold] (fragment {result.fragment_index})",
                    subtitle=f"distance: {result.distance:.4f}",
                    border_style="cyan",
                )
            )

    cli_output(build_fragment_search_result(repos, query, all_results), _print_fragments, json_output=json_output)


def run_search_documents(
    factory: ServiceFactory,
    repos: list[RepositoryConfig],
    query: str,
    n_results: int,
    json_output: bool = False,
) -> None:
    """Search for documents across one or more repositories."""
    all_results = search_documents_across_repos(factory, repos, query, n_results)

    def _print_documents():
        if not all_results:
            console.print("[dim]No results found.[/dim]")
            return
        for doc_result in all_results:
            top_fragment = doc_result.top_fragments[0] if doc_result.top_fragments else None
            if top_fragment and len(top_fragment.text) > 200:
                preview = top_fragment.text[:200] + "..."
            else:
                preview = top_fragment.text if top_fragment else ""
            console.print(
                Panel(
                    preview,
                    title=f"[bold]{doc_result.document_path}[/bold]",
                    subtitle=(
                        f"best distance: {doc_result.best_distance:.4f} | {len(doc_result.top_fragments)} fragments"
                    ),
                    border_style="green",
                )
            )

    cli_output(build_document_search_result(repos, query, all_results), _print_documents, json_output=json_output)
