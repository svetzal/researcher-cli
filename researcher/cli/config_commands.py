import typer

from researcher.cli.output import JSON_OPTION, cli_errors, cli_output, console, make_service_factory_callback
from researcher.cli.presenters import present_config
from researcher.cli.serializers import serialize_config, serialize_config_path, serialize_config_set
from researcher.exceptions import ConfigValidationError, ResearcherError
from researcher.service_factory import ServiceFactory

config_app = typer.Typer(help="Manage researcher configuration.")

make_service_factory_callback(config_app)


@config_app.command("show")
@cli_errors(ResearcherError)
def show_config(
    ctx: typer.Context,
    json_output: bool = JSON_OPTION,
) -> None:
    factory: ServiceFactory = ctx.obj
    config = factory.settings_service.get_settings()
    cli_output(
        serialize_config(config),
        lambda: present_config(config, console),
        json_output=json_output,
    )


@config_app.command("set")
@cli_errors(ConfigValidationError)
def set_config(
    ctx: typer.Context,
    key: str = typer.Argument(..., help="Configuration key (e.g. default_embedding_provider)"),
    value: str = typer.Argument(..., help="Configuration value"),
    json_output: bool = JSON_OPTION,
) -> None:
    factory: ServiceFactory = ctx.obj
    new_config = factory.settings_service.set_value(key, value)
    cli_output(
        serialize_config_set(key, getattr(new_config, key)),
        f"[green]✓[/green] Set [bold]{key}[/bold] = {value}",
        json_output=json_output,
    )


@config_app.command("path")
@cli_errors(ResearcherError)
def config_path(
    ctx: typer.Context,
    json_output: bool = JSON_OPTION,
) -> None:
    factory: ServiceFactory = ctx.obj
    path = factory.settings_service.config_file_path()
    cli_output(
        serialize_config_path(path),
        str(path),
        json_output=json_output,
    )
