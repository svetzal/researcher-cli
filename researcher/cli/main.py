from contextlib import contextmanager

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn

from researcher.cli.config_commands import config_app
from researcher.cli.init_commands import init_command
from researcher.cli.model_commands import models_app
from researcher.cli.output import (
    JSON_OPTION,
    cli_errors,
    cli_output,
    console,
    make_service_factory_callback,
    require_repos,
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
from researcher.enums import SearchMode
from researcher.exceptions import ResearcherError
from researcher.service_factory import ServiceFactory
from researcher.services.index_facade import index_repos, remove_from_repo

app = typer.Typer(
    name="researcher",
    help="Index and search document repositories with semantic search.",
    no_args_is_help=True,
)
app.add_typer(repo_app, name="repo")
app.add_typer(config_app, name="config")
app.add_typer(models_app, name="models")
app.command("init")(init_command)


make_service_factory_callback(app)


@contextmanager
def _spinner_for_repo(repo: RepositoryConfig):
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task(f"Indexing [bold]{repo.name}[/bold]...", total=None)
        yield
        progress.remove_task(task)


@app.command("index")
@cli_errors(ResearcherError)
def index_command(
    ctx: typer.Context,
    repo_name: str | None = typer.Argument(None, help="Repository name (or all if not specified)"),
    json_output: bool = JSON_OPTION,
    force: bool = typer.Option(False, "--force", help="Re-index all files, ignoring checksums"),
) -> None:
    factory: ServiceFactory = ctx.obj
    repos = require_repos(factory, repo_name, json_output=json_output)

    on_repo = None if json_output else _spinner_for_repo
    results = index_repos(factory, repos, force=force, on_repo=on_repo)

    cli_output(
        build_json_results_wrapper([serialize_index_result(name, r) for name, r in results]),
        lambda: present_index_results(results, console),
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
    factory: ServiceFactory = ctx.obj
    remove_from_repo(factory, repo_name, document_path)

    cli_output(
        {"repository": repo_name, "document_path": document_path, "removed": True},
        f"[green]✓[/green] Removed '{document_path}' from '[bold]{repo_name}[/bold]'",
        json_output=json_output,
    )


@app.command("status")
@cli_errors(ResearcherError)
def status_command(
    ctx: typer.Context,
    repo_name: str | None = typer.Argument(None, help="Repository name (or all if not specified)"),
    json_output: bool = JSON_OPTION,
) -> None:
    factory: ServiceFactory = ctx.obj
    repos = require_repos(factory, repo_name, json_output=json_output)

    stats = [factory.index_service(repo).get_stats() for repo in repos]

    cli_output(
        build_json_results_wrapper([serialize_index_stats(s) for s in stats]),
        lambda: present_status(stats, console),
        json_output=json_output,
    )


@app.command("search")
@cli_errors(ResearcherError)
def search_command(
    ctx: typer.Context,
    query: str = typer.Argument(..., help="Search query"),
    repo: str | None = typer.Option(None, "--repo", "-r", help="Limit search to this repository"),
    fragments: int = typer.Option(10, "--fragments", "-f", help="Number of fragment results"),
    documents: int = typer.Option(5, "--documents", "-d", help="Number of document results"),
    mode: SearchMode = typer.Option(
        SearchMode.DOCUMENTS, "--mode", "-m", help="Search mode: 'fragments' or 'documents'"
    ),
    json_output: bool = JSON_OPTION,
) -> None:
    factory: ServiceFactory = ctx.obj
    search_repos = require_repos(
        factory, repo, json_output=json_output, empty_payload=serialize_empty_search(query, mode, repo)
    )

    if mode == "fragments":
        run_search_fragments(factory, search_repos, query, n_results=fragments, json_output=json_output)
    else:
        run_search_documents(factory, search_repos, query, n_results=documents, json_output=json_output)


@app.command("serve")
def serve_command(
    port: int | None = typer.Option(None, "--port", "-p", help="HTTP port (default: STDIO mode)"),
) -> None:
    from researcher.mcp.server import start_server

    start_server(port=port)
