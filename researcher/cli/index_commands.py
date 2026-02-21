import json

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from researcher.config import RepositoryConfig
from researcher.service_factory import ServiceFactory

console = Console()


def run_index(factory: ServiceFactory, repo: RepositoryConfig, json_output: bool = False) -> dict:
    """Index a single repository with progress display.

    Returns a dict describing the indexing result for the repository.
    """
    if json_output:
        service = factory.index_service(repo)
        result = service.index_repository(repo)
    else:
        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task(f"Indexing [bold]{repo.name}[/bold]...", total=None)
            service = factory.index_service(repo)
            result = service.index_repository(repo)
            progress.remove_task(task)

        console.print(
            f"[green]✓[/green] [bold]{repo.name}[/bold]: {result.documents_indexed} indexed, "
            f"{result.documents_skipped} skipped, {result.documents_failed} failed, "
            f"{result.documents_purged} purged, {result.fragments_created} fragments"
        )

        if result.errors:
            for error in result.errors:
                console.print(f"  [red]✗[/red] {error}")

    return {
        "repository": repo.name,
        "documents_indexed": result.documents_indexed,
        "documents_skipped": result.documents_skipped,
        "documents_failed": result.documents_failed,
        "documents_purged": result.documents_purged,
        "fragments_created": result.fragments_created,
        "errors": result.errors,
    }


def run_status(factory: ServiceFactory, repo: RepositoryConfig, json_output: bool = False) -> dict:
    """Display index stats for a single repository.

    Returns a dict of stats for the repository.
    """
    service = factory.index_service(repo)
    stats = service.get_stats()

    if not json_output:
        table = Table(show_header=False, box=None)
        table.add_column("Key", style="bold")
        table.add_column("Value")
        table.add_row("Repository", stats.repository_name)
        table.add_row("Documents", str(stats.total_documents))
        table.add_row("Fragments", str(stats.total_fragments))
        table.add_row("Last Indexed", str(stats.last_indexed) if stats.last_indexed else "[dim]never[/dim]")
        console.print(table)

    return {
        "repository_name": stats.repository_name,
        "total_documents": stats.total_documents,
        "total_fragments": stats.total_fragments,
        "last_indexed": stats.last_indexed.isoformat() if stats.last_indexed else None,
    }


def emit_json_index_results(repo_results: list[dict]) -> None:
    """Write collected index results as a JSON object to stdout."""
    typer.echo(json.dumps({"repositories": repo_results}, default=str))


def emit_json_status_results(repo_stats: list[dict]) -> None:
    """Write collected status results as a JSON object to stdout."""
    typer.echo(json.dumps({"repositories": repo_stats}, default=str))
