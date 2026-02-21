from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from researcher.config import RepositoryConfig
from researcher.service_factory import ServiceFactory

console = Console()


def run_index(factory: ServiceFactory, repo: RepositoryConfig) -> None:
    """Index a single repository with progress display."""
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task(f"Indexing [bold]{repo.name}[/bold]...", total=None)
        service = factory.index_service(repo)
        result = service.index_repository(repo)
        progress.remove_task(task)

    console.print(
        f"[green]✓[/green] [bold]{repo.name}[/bold]: {result.documents_indexed} indexed, "
        f"{result.documents_skipped} skipped, {result.documents_failed} failed, "
        f"{result.fragments_created} fragments"
    )

    if result.errors:
        for error in result.errors:
            console.print(f"  [red]✗[/red] {error}")


def run_status(factory: ServiceFactory, repo: RepositoryConfig) -> None:
    """Display index stats for a single repository."""
    service = factory.index_service(repo)
    stats = service.get_stats()

    table = Table(show_header=False, box=None)
    table.add_column("Key", style="bold")
    table.add_column("Value")
    table.add_row("Repository", stats.repository_name)
    table.add_row("Documents", str(stats.total_documents))
    table.add_row("Fragments", str(stats.total_fragments))
    table.add_row("Last Indexed", str(stats.last_indexed) if stats.last_indexed else "[dim]never[/dim]")
    console.print(table)
