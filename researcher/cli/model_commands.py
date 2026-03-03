import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from researcher.service_factory import ServiceFactory

models_app = typer.Typer(help="Manage model caches for offline use.")
console = Console()


@models_app.command("pack")
def pack_command(
    output: Path = typer.Option(..., "--output", "-o", help="Output archive path (e.g. models.tar.gz)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Pack model cache directories into a portable archive."""
    factory = ServiceFactory()
    repos = factory.repository_service.list_repositories()

    if not repos:
        if json_output:
            typer.echo(json.dumps({"error": "No repositories configured."}))
        else:
            console.print("[yellow]No repositories configured. Use 'researcher repo add' to add one.[/yellow]")
        raise typer.Exit(1)

    service = factory.model_archive_service()

    try:
        result = service.pack(repos, output)
    except FileNotFoundError as e:
        if json_output:
            typer.echo(json.dumps({"error": str(e)}))
        else:
            console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None

    if json_output:
        data = {
            "archive": str(result.archive_path),
            "total_files": result.total_files,
            "entries": [
                {"category": entry.category, "archive_path": entry.archive_path}
                for entry in result.entries
            ],
        }
        typer.echo(json.dumps(data))
    else:
        console.print(f"[green]✓[/green] Packed [bold]{result.total_files}[/bold] files into {result.archive_path}")
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Category", no_wrap=True)
        table.add_column("Archive Path")
        for entry in result.entries:
            table.add_row(entry.category, entry.archive_path)
        console.print(table)


@models_app.command("unpack")
def unpack_command(
    archive: Path = typer.Argument(..., help="Path to the model archive (.tar.gz)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Unpack a model archive into the local cache directories."""
    factory = ServiceFactory()
    service = factory.model_archive_service()

    try:
        result = service.unpack(archive)
    except (FileNotFoundError, ValueError) as e:
        if json_output:
            typer.echo(json.dumps({"error": str(e)}))
        else:
            console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None

    if json_output:
        data = {
            "archive": str(archive),
            "entries_restored": result.entries_restored,
            "files_extracted": result.files_extracted,
        }
        typer.echo(json.dumps(data))
    else:
        console.print(
            f"[green]✓[/green] Unpacked [bold]{result.files_extracted}[/bold] files "
            f"across [bold]{result.entries_restored}[/bold] model entries from {archive}"
        )
