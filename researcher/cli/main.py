import typer
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from researcher.cli.config_commands import config_app
from researcher.cli.index_commands import build_json_results_wrapper, run_index, run_status
from researcher.cli.init_commands import init_command
from researcher.cli.model_commands import models_app
from researcher.cli.output import JSON_OPTION, cli_exit_on_error, cli_output, console, make_service_factory_callback
from researcher.cli.repo_commands import repo_app
from researcher.cli.search_commands import run_search_documents, run_search_fragments
from researcher.config import RepositoryConfig
from researcher.exceptions import ResearcherError
from researcher.service_factory import ServiceFactory

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


make_service_factory_callback(app)


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

    if repo_name:
        with cli_exit_on_error(ValueError, ResearcherError, json_output=json_output):
            repos = _resolve_repos(factory, repo_name, repos)

    repo_results: list[dict] = []

    def _run_with_progress():
        for repo in repos:
            with Progress(
                SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
            ) as progress:
                task = progress.add_task(f"Indexing [bold]{repo.name}[/bold]...", total=None)
                result = run_index(factory, repo, force=force)
                progress.remove_task(task)
            repo_results.append(result)
            console.print(
                f"[green]✓[/green] [bold]{result['repository']}[/bold]: {result['documents_indexed']} indexed, "
                f"{result['documents_skipped']} skipped, {result['documents_failed']} failed, "
                f"{result['documents_purged']} purged, {result['fragments_created']} fragments"
            )
            for error in result["errors"]:
                console.print(f"  [red]✗[/red] {error}")

    if json_output:
        repo_results = [run_index(factory, repo, force=force) for repo in repos]

    cli_output(
        build_json_results_wrapper(repo_results),
        _run_with_progress,
        json_output=json_output,
    )


@app.command("remove")
def remove_command(
    ctx: typer.Context,
    repo_name: str = typer.Argument(..., help="Repository name"),
    document_path: str = typer.Argument(..., help="Document path to remove from the index"),
    json_output: bool = JSON_OPTION,
) -> None:
    """Remove a specific document from the index."""
    factory: ServiceFactory = ctx.obj
    with cli_exit_on_error(ValueError, ResearcherError, json_output=json_output):
        repo = factory.repository_service.get_repository(repo_name)

    with cli_exit_on_error(ResearcherError, json_output=json_output):
        service = factory.index_service(repo)
        service.remove_document(document_path)

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

    if repo_name:
        with cli_exit_on_error(ValueError, ResearcherError, json_output=json_output):
            repos = _resolve_repos(factory, repo_name, repos)

    repo_stats = [run_status(factory, repo) for repo in repos]

    def _print_status():
        for stat in repo_stats:
            table = Table(show_header=False, box=None)
            table.add_column("Key", style="bold")
            table.add_column("Value")
            table.add_row("Repository", stat["repository_name"])
            table.add_row("Documents", str(stat["total_documents"]))
            table.add_row("Fragments", str(stat["total_fragments"]))
            table.add_row("Last Indexed", stat["last_indexed"] or "[dim]never[/dim]")
            console.print(table)

    cli_output(
        build_json_results_wrapper(repo_stats),
        _print_status,
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
            {
                "query": query,
                "mode": mode,
                "repository": repo,
                "repos_searched": [],
                "result_count": 0,
                "results": [],
            },
            "[yellow]No repositories configured.[/yellow]",
            json_output=json_output,
        )
        raise typer.Exit(0)

    with cli_exit_on_error(ValueError, ResearcherError, json_output=json_output):
        search_repos = _resolve_repos(factory, repo, all_repos)

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
