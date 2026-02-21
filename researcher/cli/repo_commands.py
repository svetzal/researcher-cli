import typer
from rich.console import Console
from rich.table import Table

from researcher.service_factory import ServiceFactory

repo_app = typer.Typer(help="Manage document repositories.")
console = Console()


@repo_app.command("add")
def add_repo(
    name: str = typer.Argument(..., help="Repository name"),
    path: str = typer.Argument(..., help="Path to the document directory"),
    file_types: str = typer.Option("md,txt,pdf,docx,html", "--file-types", help="Comma-separated file extensions"),
    embedding_provider: str = typer.Option("chromadb", "--embedding-provider", help="Embedding provider"),
    embedding_model: str = typer.Option(None, "--embedding-model", help="Embedding model name"),
) -> None:
    """Add a new document repository."""
    factory = ServiceFactory()
    types = [t.strip() for t in file_types.split(",")]
    try:
        repo = factory.repository_service.add_repository(
            name=name,
            path=path,
            file_types=types,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
        )
        console.print(f"[green]✓[/green] Added repository '[bold]{repo.name}[/bold]' at {repo.path}")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@repo_app.command("remove")
def remove_repo(
    name: str = typer.Argument(..., help="Repository name to remove"),
) -> None:
    """Remove a document repository."""
    factory = ServiceFactory()
    try:
        factory.repository_service.remove_repository(name)
        console.print(f"[green]✓[/green] Removed repository '[bold]{name}[/bold]'")
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@repo_app.command("list")
def list_repos() -> None:
    """List all configured repositories."""
    factory = ServiceFactory()
    repos = factory.repository_service.list_repositories()

    if not repos:
        console.print("[dim]No repositories configured.[/dim]")
        return

    table = Table(title="Repositories", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="bold")
    table.add_column("Path")
    table.add_column("File Types")
    table.add_column("Embedding Provider")
    table.add_column("Model")

    for repo in repos:
        table.add_row(
            repo.name,
            repo.path,
            ", ".join(repo.file_types),
            repo.embedding_provider,
            repo.embedding_model or "[dim]default[/dim]",
        )

    console.print(table)
