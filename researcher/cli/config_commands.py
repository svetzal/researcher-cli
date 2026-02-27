import typer
import yaml
from rich.console import Console
from rich.syntax import Syntax

from researcher.config import ResearcherConfig
from researcher.service_factory import ServiceFactory

config_app = typer.Typer(help="Manage researcher configuration.")
console = Console()


@config_app.command("show")
def show_config() -> None:
    """Display the current configuration."""
    factory = ServiceFactory()
    config = factory.config
    yaml_text = yaml.dump(config.model_dump(mode="json"), default_flow_style=False)
    syntax = Syntax(yaml_text, "yaml", theme="monokai", line_numbers=False)
    console.print(syntax)


@config_app.command("set")
def set_config(
    key: str = typer.Argument(..., help="Configuration key (e.g. default_embedding_provider)"),
    value: str = typer.Argument(..., help="Configuration value"),
) -> None:
    """Set a top-level configuration value."""
    factory = ServiceFactory()
    config = factory.config
    data = config.model_dump(mode="json")

    if key not in data:
        console.print(f"[red]Error:[/red] Unknown configuration key: '{key}'")
        raise typer.Exit(1)

    if isinstance(data[key], int):
        try:
            data[key] = int(value)
        except ValueError:
            console.print(f"[red]Error:[/red] Value for '{key}' must be an integer")
            raise typer.Exit(1) from None
    else:
        data[key] = value

    new_config = ResearcherConfig.model_validate(data)
    factory.config_gateway.save(new_config)
    console.print(f"[green]✓[/green] Set [bold]{key}[/bold] = {value}")


@config_app.command("path")
def config_path() -> None:
    """Show the path to the configuration file."""
    factory = ServiceFactory()
    config_file = factory.config_gateway.config_dir / "config.yaml"
    console.print(str(config_file))
