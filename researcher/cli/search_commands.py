from researcher.cli.output import cli_output, console
from researcher.cli.presenters import present_document_results, present_fragment_results
from researcher.cli.serializers import serialize_document_search, serialize_fragment_search
from researcher.config import RepositoryConfig
from researcher.service_factory import ServiceFactory
from researcher.services.multi_repo_search import (
    search_documents_across_repos,
    search_fragments_across_repos,
)


def run_search_fragments(
    factory: ServiceFactory,
    repos: list[RepositoryConfig],
    query: str,
    n_results: int,
    json_output: bool = False,
) -> None:
    all_results = search_fragments_across_repos(factory, repos, query, n_results)
    cli_output(
        serialize_fragment_search(repos, query, all_results),
        lambda: present_fragment_results(all_results, console),
        json_output=json_output,
    )


def run_search_documents(
    factory: ServiceFactory,
    repos: list[RepositoryConfig],
    query: str,
    n_results: int,
    json_output: bool = False,
) -> None:
    all_results = search_documents_across_repos(factory, repos, query, n_results)
    cli_output(
        serialize_document_search(repos, query, all_results),
        lambda: present_document_results(all_results, console),
        json_output=json_output,
    )
