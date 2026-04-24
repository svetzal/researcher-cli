import typer
from rich.progress import Progress, SpinnerColumn, TextColumn

from researcher.cli.config_commands import config_app
from researcher.cli.init_commands import init_command
from researcher.cli.model_commands import models_app
from researcher.cli.output import (
    JSON_OPTION,
    cli_errors,
    cli_exit_on_error,
    cli_output,
    console,
    make_service_factory_callback,
)
from researcher.cli.presenters import present_index_results, present_status
from researcher.cli.repo_commands import repo_app
from researcher.cli.search_commands import run_search_documents, run_search_fragments
from researcher.cli.serializers import (
    build_json_results_wrapper,
    serialize_empty_search,
    serialize_index_result,
    serialize_index_stats,
)
from researcher.config import RepositoryConfig
from researcher.exceptions import ResearcherError
from researcher.models import IndexingResult
from researcher.service_factory import ServiceFactory
from researcher.services.index_facade import remove_from_repo

app = typer.Typer(
    name="researcher",
    help="Index and search document repositories with semantic search.",
    no_args_is_help=True,
)
app.add_typer(repo_app, name="repo")
app.add_typer(config_app, name="config")
app.add_typer(models_app, name="models")
app.command("init")(init_command)


def _resolve_repos(
    factory: ServiceFactory,
    repo_name: str | None,
    all_repos: list[RepositoryConfig],
) -> list[RepositoryConfig]:
    """Return [named_repo] if repo_name given, else all_repos.

    Raises ValueError if repo_name is given but not found.
    """
    if repo_name:
        return [factory.repository_service.get_repository(repo_name)]
    return all_repos


def _resolve_repos_or_exit(
    factory: ServiceFactory,
    repo_name: str | None,
    all_repos: list[RepositoryConfig],
    json_output: bool,
) -> list[RepositoryConfig]:
    with cli_exit_on_error(ValueError, ResearcherError, json_output=json_output):
        return _resolve_repos(factory, repo_name, all_repos)


make_service_factory_callback(app)


def _index_with_spinner(factory: ServiceFactory, repo: RepositoryConfig, force: bool) -> IndexingResult:
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task(f"Indexing [bold]{repo.name}[/bold]...", total=None)
        result = factory.index_service(repo).index_repository(repo, force=force)
        progress.remove_task(task)
    return result


@app.command("index")
def index_command(
    ctx: typer.Context,
    repo_name: str | None = typer.Argument(None, help="Repository name (or all if not specified)"),
    json_output: bool = JSON_OPTION,
    force: bool = typer.Option(False, "--force", help="Re-index all files, ignoring checksums"),
) -> None:
    """Index a repository (or all repositories)."""
    factory: ServiceFactory = ctx.obj
    repos = factory.repository_service.list_repositories()

    if not repos:
        cli_output(
            {"repositories": []},
            "[yellow]No repositories configured. Use 'researcher repo add' to add one.[/yellow]",
            json_output=json_output,
        )
        raise typer.Exit(0)

    repos = _resolve_repos_or_exit(factory, repo_name, repos, json_output)

    repo_results: list[dict] = []
    for repo in repos:
        if json_output:
            result = factory.index_service(repo).index_repository(repo, force=force)
        else:
            result = _index_with_spinner(factory, repo, force)
        repo_results.append(serialize_index_result(repo.name, result))

    cli_output(
        build_json_results_wrapper(repo_results),
        lambda: present_index_results(repo_results, console),
        json_output=json_output,
    )


@app.command("remove")
@cli_errors(ValueError, ResearcherError)
def remove_command(
    ctx: typer.Context,
    repo_name: str = typer.Argument(..., help="Repository name"),
    document_path: str = typer.Argument(..., help="Document path to remove from the index"),
    json_output: bool = JSON_OPTION,
) -> None:
    """Remove a specific document from the index."""
    factory: ServiceFactory = ctx.obj
    remove_from_repo(factory, repo_name, document_path)

    cli_output(
        {"repository": repo_name, "document_path": document_path, "removed": True},
        f"[green]✓[/green] Removed '{document_path}' from '[bold]{repo_name}[/bold]'",
        json_output=json_output,
    )


@app.command("status")
def status_command(
    ctx: typer.Context,
    repo_name: str | None = typer.Argument(None, help="Repository name (or all if not specified)"),
    json_output: bool = JSON_OPTION,
) -> None:
    """Show index statistics for repositories."""
    factory: ServiceFactory = ctx.obj
    repos = factory.repository_service.list_repositories()

    if not repos:
        cli_output({"repositories": []}, "[dim]No repositories configured.[/dim]", json_output=json_output)
        return

    repos = _resolve_repos_or_exit(factory, repo_name, repos, json_output)

    repo_stats = [serialize_index_stats(factory.index_service(repo).get_stats()) for repo in repos]

    cli_output(
        build_json_results_wrapper(repo_stats),
        lambda: present_status(repo_stats, console),
        json_output=json_output,
    )


@app.command("search")
def search_command(
    ctx: typer.Context,
    query: str = typer.Argument(..., help="Search query"),
    repo: str | None = typer.Option(None, "--repo", "-r", help="Limit search to this repository"),
    fragments: int = typer.Option(10, "--fragments", "-f", help="Number of fragment results"),
    documents: int = typer.Option(5, "--documents", "-d", help="Number of document results"),
    mode: str = typer.Option("documents", "--mode", "-m", help="Search mode: 'fragments' or 'documents'"),
    json_output: bool = JSON_OPTION,
) -> None:
    """Search across indexed repositories."""
    factory: ServiceFactory = ctx.obj
    all_repos = factory.repository_service.list_repositories()

    if not all_repos:
        cli_output(
            serialize_empty_search(query, mode, repo),
            "[yellow]No repositories configured.[/yellow]",
            json_output=json_output,
        )
        raise typer.Exit(0)

    search_repos = _resolve_repos_or_exit(factory, repo, all_repos, json_output)

    with cli_exit_on_error(ResearcherError, json_output=json_output):
        if mode == "fragments":
            run_search_fragments(factory, search_repos, query, n_results=fragments, json_output=json_output)
        else:
            run_search_documents(factory, search_repos, query, n_results=documents, json_output=json_output)


@app.command("serve")
def serve_command(
    port: int | None = typer.Option(None, "--port", "-p", help="HTTP port (default: STDIO mode)"),
) -> None:
    """Start the MCP server."""
    from researcher.mcp.server import start_server

    start_server(port=port)
