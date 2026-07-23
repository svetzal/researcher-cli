from researcher.cli.output import cli_output, console
from researcher.cli.presenters import present_document_results, present_fragment_results
from researcher.cli.serializers import serialize_document_search, serialize_fragment_search
from researcher.config import RepositoryConfig
from researcher.service_factory import ServiceFactory
from researcher.services.multi_repo_search import (
    search_documents_across_repos,
    search_fragments_across_repos,
)


def _warn_unavailable_repos(failed_repositories: list[str], *, json_output: bool) -> None:
    if not failed_repositories or json_output:
        return
    names = ", ".join(failed_repositories)
    console.print(f"[yellow]Warning: {len(failed_repositories)} repositories unavailable: {names}[/yellow]")


def run_search_fragments(
    factory: ServiceFactory,
    repos: list[RepositoryConfig],
    query: str,
    n_results: int,
    json_output: bool = False,
) -> None:
    outcome = search_fragments_across_repos(factory, repos, query, n_results)
    _warn_unavailable_repos(outcome.failed_repositories, json_output=json_output)
    cli_output(
        serialize_fragment_search(repos, query, outcome.results, outcome.failed_repositories),
        lambda: present_fragment_results(outcome.results, console),
        json_output=json_output,
    )


def run_search_documents(
    factory: ServiceFactory,
    repos: list[RepositoryConfig],
    query: str,
    n_results: int,
    json_output: bool = False,
) -> None:
    outcome = search_documents_across_repos(factory, repos, query, n_results)
    _warn_unavailable_repos(outcome.failed_repositories, json_output=json_output)
    cli_output(
        serialize_document_search(repos, query, outcome.results, outcome.failed_repositories),
        lambda: present_document_results(outcome.results, console),
        json_output=json_output,
    )
