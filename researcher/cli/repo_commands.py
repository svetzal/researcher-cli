import typer
from rich.console import Console
from rich.table import Table

from researcher.cli.output import cli_exit_on_error, cli_output, make_service_factory_callback
from researcher.config import RepositoryConfig
from researcher.exceptions import RepositoryAlreadyExistsError, RepositoryNotFoundError
from researcher.model_registry import API_ONLY_PRESETS, VLM_PRESET_REPOS
from researcher.service_factory import ServiceFactory

_DEFAULTS = RepositoryConfig(name="", path="")
_vlm_names = ", ".join(sorted(set(VLM_PRESET_REPOS.keys()) | API_ONLY_PRESETS))

repo_app = typer.Typer(help="Manage document repositories.")
console = Console()


make_service_factory_callback(repo_app)


@repo_app.command("add")
def add_repo(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Repository name"),
    path: str = typer.Argument(..., help="Path to the document directory"),
    file_types: str = typer.Option(
        ",".join(_DEFAULTS.file_types), "--file-types", help="Comma-separated file extensions"
    ),
    embedding_provider: str = typer.Option(
        _DEFAULTS.embedding_provider, "--embedding-provider", help="Embedding provider"
    ),
    embedding_model: str = typer.Option(None, "--embedding-model", help="Embedding model name"),
    exclude: list[str] = typer.Option(
        None,
        "--exclude",
        "-e",
        help="Glob pattern to exclude (repeatable, e.g. --exclude node_modules --exclude '.*')",
    ),
    image_pipeline: str = typer.Option(
        _DEFAULTS.image_pipeline,
        "--image-pipeline",
        help="Image processing pipeline: 'standard' (OCR) or 'vlm' (Vision Language Model)",
    ),
    image_vlm_model: str = typer.Option(
        None,
        "--image-vlm-model",
        help=(
            f"VLM preset name (only used when --image-pipeline=vlm). Available: {_vlm_names}. Default: granite_docling"
        ),
    ),
    audio_asr_model: str = typer.Option(
        None,
        "--audio-asr-model",
        help="Whisper ASR model for audio files. Options: tiny, base, small, medium, large, turbo. Default: turbo",
    ),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Add a new document repository."""
    factory: ServiceFactory = ctx.obj
    types = [t.strip() for t in file_types.split(",")]
    with cli_exit_on_error(RepositoryAlreadyExistsError, json_output=json_output):
        repo = factory.repository_service.add_repository(
            name=name,
            path=path,
            file_types=types,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
            exclude_patterns=exclude or [],
            image_pipeline=image_pipeline,
            image_vlm_model=image_vlm_model,
            audio_asr_model=audio_asr_model,
        )
        cli_output(
            repo.model_dump(),
            f"[green]✓[/green] Added repository '[bold]{repo.name}[/bold]' at {repo.path}",
            json_output=json_output,
        )


@repo_app.command("remove")
def remove_repo(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Repository name to remove"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Remove a document repository."""
    factory: ServiceFactory = ctx.obj
    with cli_exit_on_error(RepositoryNotFoundError, json_output=json_output):
        factory.repository_service.remove_repository(name)
        cli_output(
            {"name": name, "removed": True},
            f"[green]✓[/green] Removed repository '[bold]{name}[/bold]'",
            json_output=json_output,
        )


@repo_app.command("update")
def update_repo(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Repository name"),
    file_types: str = typer.Option(None, "--file-types", help="Comma-separated file extensions (replaces existing)"),
    embedding_provider: str = typer.Option(None, "--embedding-provider", help="Embedding provider"),
    embedding_model: str = typer.Option(None, "--embedding-model", help="Embedding model name"),
    exclude: list[str] = typer.Option(
        None,
        "--exclude",
        "-e",
        help="Glob pattern to add to exclusions (repeatable). New patterns are added to the existing list.",
    ),
    no_purge: bool = typer.Option(
        False,
        "--no-purge",
        help="Skip purging previously-indexed files that match the new exclusion patterns.",
    ),
    image_pipeline: str = typer.Option(
        None,
        "--image-pipeline",
        help="Image processing pipeline: 'standard' (OCR) or 'vlm' (Vision Language Model)",
    ),
    image_vlm_model: str = typer.Option(
        None,
        "--image-vlm-model",
        help=(
            f"VLM preset name (only used when --image-pipeline=vlm). Available: {_vlm_names}. Default: granite_docling"
        ),
    ),
    audio_asr_model: str = typer.Option(
        None,
        "--audio-asr-model",
        help="Whisper ASR model for audio files. Options: tiny, base, small, medium, large, turbo. Default: turbo",
    ),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Update an existing repository's configuration."""
    factory: ServiceFactory = ctx.obj
    types = [t.strip() for t in file_types.split(",")] if file_types else None
    with cli_exit_on_error(RepositoryNotFoundError, json_output=json_output):
        repo, added_patterns = factory.repository_service.update_repository(
            name=name,
            file_types=types,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
            add_exclude_patterns=exclude or [],
            image_pipeline=image_pipeline,
            image_vlm_model=image_vlm_model,
            audio_asr_model=audio_asr_model,
        )
        purged = 0
        if added_patterns and not no_purge:
            index_svc = factory.index_service(repo)
            purged = index_svc.purge_excluded_documents(repo)

        def _print_update():
            console.print(f"[green]✓[/green] Updated repository '[bold]{repo.name}[/bold]'")
            if added_patterns:
                console.print(f"  Added exclusion patterns: {', '.join(added_patterns)}")
            if purged:
                console.print(f"  Purged [bold]{purged}[/bold] previously-indexed document(s) matching new exclusions")
            elif added_patterns and not no_purge:
                console.print("  [dim]No previously-indexed documents matched the new exclusions[/dim]")

        cli_output(
            repo.model_dump() | {"purged_documents": purged},
            _print_update,
            json_output=json_output,
        )


@repo_app.command("list")
def list_repos(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """List all configured repositories."""
    factory: ServiceFactory = ctx.obj
    repos = factory.repository_service.list_repositories()

    def _print_repos():
        if not repos:
            console.print("[dim]No repositories configured.[/dim]")
            return

        table = Table(title="Repositories", show_header=True, header_style="bold cyan", expand=True)
        table.add_column("Name", style="bold", no_wrap=True)
        table.add_column("Path")
        table.add_column("File Types")
        table.add_column("Embed", no_wrap=True)
        table.add_column("Image", no_wrap=True)
        table.add_column("Excludes")

        for repo in repos:
            embed_info = repo.embedding_provider
            if repo.embedding_model:
                embed_info += f"\n{repo.embedding_model}"

            image_info = repo.image_pipeline
            if repo.image_pipeline == "vlm" and repo.image_vlm_model:
                image_info += f"\n{repo.image_vlm_model}"

            table.add_row(
                repo.name,
                repo.path,
                ", ".join(repo.file_types),
                embed_info,
                image_info,
                ", ".join(repo.exclude_patterns) if repo.exclude_patterns else "[dim]none[/dim]",
            )

        console.print(table)

    cli_output(
        {"repositories": [repo.model_dump() for repo in repos]},
        _print_repos,
        json_output=json_output,
    )
