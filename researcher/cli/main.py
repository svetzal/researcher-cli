import json
from typing import Optional

import typer
from rich.console import Console

from researcher.cli.config_commands import config_app
from researcher.cli.index_commands import emit_json_index_results, emit_json_status_results, run_index, run_status
from researcher.cli.repo_commands import repo_app
from researcher.cli.search_commands import run_search_documents, run_search_fragments
from researcher.service_factory import ServiceFactory

app = typer.Typer(
    name="researcher",
    help="Index and search document repositories with semantic search.",
    no_args_is_help=True,
)
app.add_typer(repo_app, name="repo")
app.add_typer(config_app, name="config")

console = Console()


@app.command("index")
def index_command(
    repo_name: Optional[str] = typer.Argument(None, help="Repository name (or all if not specified)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Index a repository (or all repositories)."""
    factory = ServiceFactory()
    repos = factory.repository_service.list_repositories()

    if not repos:
        if json_output:
            typer.echo(json.dumps({"repositories": []}))
        else:
            console.print("[yellow]No repositories configured. Use 'researcher repo add' to add one.[/yellow]")
        raise typer.Exit(0)

    if repo_name:
        try:
            target = factory.repository_service.get_repository(repo_name)
            repos = [target]
        except ValueError as e:
            if json_output:
                typer.echo(json.dumps({"error": str(e)}))
            else:
                console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    repo_results = [run_index(factory, repo, json_output=json_output) for repo in repos]

    if json_output:
        emit_json_index_results(repo_results)


@app.command("remove")
def remove_command(
    repo_name: str = typer.Argument(..., help="Repository name"),
    document_path: str = typer.Argument(..., help="Document path to remove from the index"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Remove a specific document from the index."""
    factory = ServiceFactory()
    try:
        repo = factory.repository_service.get_repository(repo_name)
    except ValueError as e:
        if json_output:
            typer.echo(json.dumps({"error": str(e)}))
        else:
            console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    service = factory.index_service(repo)
    service.remove_document(document_path)

    if json_output:
        typer.echo(json.dumps({"repository": repo_name, "document_path": document_path, "removed": True}))
    else:
        console.print(f"[green]✓[/green] Removed '{document_path}' from '[bold]{repo_name}[/bold]'")


@app.command("status")
def status_command(
    repo_name: Optional[str] = typer.Argument(None, help="Repository name (or all if not specified)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Show index statistics for repositories."""
    factory = ServiceFactory()
    repos = factory.repository_service.list_repositories()

    if not repos:
        if json_output:
            typer.echo(json.dumps({"repositories": []}))
        else:
            console.print("[dim]No repositories configured.[/dim]")
        return

    if repo_name:
        try:
            target = factory.repository_service.get_repository(repo_name)
            repos = [target]
        except ValueError as e:
            if json_output:
                typer.echo(json.dumps({"error": str(e)}))
            else:
                console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    repo_stats = [run_status(factory, repo, json_output=json_output) for repo in repos]

    if json_output:
        emit_json_status_results(repo_stats)


@app.command("search")
def search_command(
    query: str = typer.Argument(..., help="Search query"),
    repo: Optional[str] = typer.Option(None, "--repo", "-r", help="Limit search to this repository"),
    fragments: int = typer.Option(10, "--fragments", "-f", help="Number of fragment results"),
    documents: int = typer.Option(5, "--documents", "-d", help="Number of document results"),
    mode: str = typer.Option("documents", "--mode", "-m", help="Search mode: 'fragments' or 'documents'"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Search across indexed repositories."""
    factory = ServiceFactory()
    all_repos = factory.repository_service.list_repositories()

    if not all_repos:
        if json_output:
            empty: dict = {
                "query": query,
                "mode": mode,
                "repository": repo,
                "repos_searched": [],
                "result_count": 0,
                "results": [],
            }
            typer.echo(json.dumps(empty))
        else:
            console.print("[yellow]No repositories configured.[/yellow]")
        raise typer.Exit(0)

    if repo:
        try:
            target = factory.repository_service.get_repository(repo)
            search_repos = [target]
        except ValueError as e:
            if json_output:
                typer.echo(json.dumps({"error": str(e)}))
            else:
                console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)
    else:
        search_repos = all_repos

    if mode == "fragments":
        run_search_fragments(factory, search_repos, query, n_results=fragments, json_output=json_output)
    else:
        run_search_documents(factory, search_repos, query, n_results=documents, json_output=json_output)


@app.command("serve")
def serve_command(
    port: Optional[int] = typer.Option(None, "--port", "-p", help="HTTP port (default: STDIO mode)"),
) -> None:
    """Start the MCP server."""
    from researcher.mcp.server import start_server

    start_server(port=port)
