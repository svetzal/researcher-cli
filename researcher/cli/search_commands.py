from researcher.cli.output import cli_output, console
from researcher.cli.presenters import present_document_results, present_fragment_results
from researcher.cli.serializers import serialize_search
from researcher.config import RepositoryConfig
from researcher.enums import SearchMode
from researcher.service_factory import ServiceFactory
from researcher.services.multi_repo_search import search_across_repos

_PRESENTER_BY_MODE = {
    SearchMode.FRAGMENTS: present_fragment_results,
    SearchMode.DOCUMENTS: present_document_results,
}


def _warn_unavailable_repos(failed_repositories: list[str], *, json_output: bool) -> None:
    if not failed_repositories or json_output:
        return
    names = ", ".join(failed_repositories)
    console.print(f"[yellow]Warning: {len(failed_repositories)} repositories unavailable: {names}[/yellow]")


def run_search(
    factory: ServiceFactory,
    repos: list[RepositoryConfig],
    query: str,
    n_results: int,
    mode: SearchMode,
    json_output: bool = False,
) -> None:
    outcome = search_across_repos(factory, repos, query, n_results, mode)
    _warn_unavailable_repos(outcome.failed_repositories, json_output=json_output)
    present = _PRESENTER_BY_MODE[mode]
    cli_output(
        serialize_search(repos, query, outcome.results, mode, outcome.failed_repositories),
        lambda: present(outcome.results, console),
        json_output=json_output,
    )
