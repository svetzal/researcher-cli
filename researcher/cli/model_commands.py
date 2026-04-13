from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from researcher.cli.output import cli_error, cli_exit_on_error, cli_output, make_service_factory_callback
from researcher.exceptions import ModelArchiveError
from researcher.service_factory import ServiceFactory

models_app = typer.Typer(help="Manage model caches for offline use.")
console = Console()


make_service_factory_callback(models_app)


@models_app.command("pack")
def pack_command(
    ctx: typer.Context,
    output: Path = typer.Option(..., "--output", "-o", help="Output archive path (e.g. models.tar.gz)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Pack model cache directories into a portable archive."""
    factory: ServiceFactory = ctx.obj
    repos = factory.repository_service.list_repositories()

    if not repos:
        cli_error("No repositories configured.", json_output=json_output)
        raise typer.Exit(1)

    service = factory.model_archive_service()

    with cli_exit_on_error(ModelArchiveError, json_output=json_output):
        result = service.pack(repos, output)

    def _print_pack():
        console.print(f"[green]✓[/green] Packed [bold]{result.total_files}[/bold] files into {result.archive_path}")
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Category", no_wrap=True)
        table.add_column("Archive Path")
        for entry in result.entries:
            table.add_row(entry.category, entry.archive_path)
        console.print(table)

    cli_output(
        {
            "archive": str(result.archive_path),
            "total_files": result.total_files,
            "entries": [{"category": entry.category, "archive_path": entry.archive_path} for entry in result.entries],
        },
        _print_pack,
        json_output=json_output,
    )


@models_app.command("unpack")
def unpack_command(
    ctx: typer.Context,
    archive: Path = typer.Argument(..., help="Path to the model archive (.tar.gz)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Unpack a model archive into the local cache directories."""
    factory: ServiceFactory = ctx.obj
    service = factory.model_archive_service()

    with cli_exit_on_error(ModelArchiveError, json_output=json_output):
        result = service.unpack(archive)

    cli_output(
        {
            "archive": str(archive),
            "entries_restored": result.entries_restored,
            "files_extracted": result.files_extracted,
        },
        f"[green]✓[/green] Unpacked [bold]{result.files_extracted}[/bold] files "
        f"across [bold]{result.entries_restored}[/bold] model entries from {archive}",
        json_output=json_output,
    )
