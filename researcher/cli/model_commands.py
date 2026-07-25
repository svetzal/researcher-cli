from pathlib import Path

import typer

from researcher.cli.output import (
    JSON_OPTION,
    cli_errors,
    cli_output,
    console,
    make_service_factory_callback,
    require_repos,
)
from researcher.cli.presenters import present_pack_result
from researcher.cli.serializers import serialize_pack_result, serialize_unpack_result
from researcher.exceptions import ResearcherError
from researcher.service_factory import ServiceFactory

models_app = typer.Typer(help="Manage model caches for offline use.")

make_service_factory_callback(models_app)


@models_app.command("pack")
@cli_errors(ResearcherError)
def pack_command(
    ctx: typer.Context,
    output: Path = typer.Option(..., "--output", "-o", help="Output archive path (e.g. models.tar.gz)"),
    json_output: bool = JSON_OPTION,
) -> None:
    factory: ServiceFactory = ctx.obj
    repos = require_repos(factory, json_output=json_output)

    service = factory.model_archive_service()
    result = service.pack(repos, output)

    cli_output(
        serialize_pack_result(result),
        lambda: present_pack_result(result, console),
        json_output=json_output,
    )


@models_app.command("unpack")
@cli_errors(ResearcherError)
def unpack_command(
    ctx: typer.Context,
    archive: Path = typer.Argument(..., help="Path to the model archive (.tar.gz)"),
    json_output: bool = JSON_OPTION,
) -> None:
    factory: ServiceFactory = ctx.obj
    service = factory.model_archive_service()
    result = service.unpack(archive)

    cli_output(
        serialize_unpack_result(archive, result),
        f"[green]✓[/green] Unpacked [bold]{result.files_extracted}[/bold] files "
        f"across [bold]{result.entries_restored}[/bold] model entries from {archive}",
        json_output=json_output,
    )
