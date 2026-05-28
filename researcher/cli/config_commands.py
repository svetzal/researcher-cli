import typer
import yaml
from rich.syntax import Syntax

from researcher.cli.output import cli_errors, console, make_service_factory_callback
from researcher.config import ResearcherConfig
from researcher.service_factory import ServiceFactory

config_app = typer.Typer(help="Manage researcher configuration.")

make_service_factory_callback(config_app)


@config_app.command("show")
def show_config(ctx: typer.Context) -> None:
    factory: ServiceFactory = ctx.obj
    config = factory.config
    yaml_text = yaml.dump(config.model_dump(mode="json"), default_flow_style=False)
    syntax = Syntax(yaml_text, "yaml", theme="monokai", line_numbers=False)
    console.print(syntax)


@config_app.command("set")
@cli_errors(ValueError)
def set_config(
    ctx: typer.Context,
    key: str = typer.Argument(..., help="Configuration key (e.g. default_embedding_provider)"),
    value: str = typer.Argument(..., help="Configuration value"),
) -> None:
    factory: ServiceFactory = ctx.obj
    config = factory.config
    data = config.model_dump(mode="json")

    if key not in data:
        raise ValueError(f"Unknown configuration key: '{key}'")
    if isinstance(data[key], int):
        try:
            data[key] = int(value)
        except ValueError:
            raise ValueError(f"Value for '{key}' must be an integer") from None
    else:
        data[key] = value

    new_config = ResearcherConfig.model_validate(data)
    factory.config_gateway.save(new_config)
    console.print(f"[green]✓[/green] Set [bold]{key}[/bold] = {value}")


@config_app.command("path")
def config_path(ctx: typer.Context) -> None:
    factory: ServiceFactory = ctx.obj
    config_file = factory.config_gateway.config_dir / "config.yaml"
    console.print(str(config_file))
