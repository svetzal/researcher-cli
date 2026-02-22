import json

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
    exclude: list[str] = typer.Option(
        None,
        "--exclude",
        "-e",
        help="Glob pattern to exclude (repeatable, e.g. --exclude node_modules --exclude '.*')",
    ),
    image_pipeline: str = typer.Option(
        "standard",
        "--image-pipeline",
        help="Image processing pipeline: 'standard' (OCR) or 'vlm' (Vision Language Model)",
    ),
    image_vlm_model: str = typer.Option(
        None,
        "--image-vlm-model",
        help=(
            "VLM preset name (only used when --image-pipeline=vlm). "
            "Available: smoldocling, granite_docling, deepseek_ocr, granite_vision, pixtral, "
            "got_ocr, phi4, qwen, gemma_12b, gemma_27b, dolphin. Default: granite_docling"
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
    factory = ServiceFactory()
    types = [t.strip() for t in file_types.split(",")]
    try:
        repo = factory.repository_service.add_repository(
            name=name,
            path=path,
            file_types=types,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
            exclude_patterns=exclude or [],
            image_pipeline=image_pipeline,
            image_vlm_model=image_vlm_model,
            audio_asr_model=audio_asr_model or "turbo",
        )
        if json_output:
            data = {
                "name": repo.name,
                "path": repo.path,
                "file_types": repo.file_types,
                "embedding_provider": repo.embedding_provider,
                "embedding_model": repo.embedding_model,
                "exclude_patterns": repo.exclude_patterns,
                "image_pipeline": repo.image_pipeline,
                "image_vlm_model": repo.image_vlm_model,
                "audio_asr_model": repo.audio_asr_model,
            }
            typer.echo(json.dumps(data, default=str))
        else:
            console.print(f"[green]✓[/green] Added repository '[bold]{repo.name}[/bold]' at {repo.path}")
    except ValueError as e:
        if json_output:
            typer.echo(json.dumps({"error": str(e)}))
        else:
            console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@repo_app.command("remove")
def remove_repo(
    name: str = typer.Argument(..., help="Repository name to remove"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Remove a document repository."""
    factory = ServiceFactory()
    try:
        factory.repository_service.remove_repository(name)
        if json_output:
            typer.echo(json.dumps({"name": name, "removed": True}))
        else:
            console.print(f"[green]✓[/green] Removed repository '[bold]{name}[/bold]'")
    except ValueError as e:
        if json_output:
            typer.echo(json.dumps({"error": str(e)}))
        else:
            console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@repo_app.command("update")
def update_repo(
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
            "VLM preset name (only used when --image-pipeline=vlm). "
            "Available: smoldocling, granite_docling, deepseek_ocr, granite_vision, pixtral, "
            "got_ocr, phi4, qwen, gemma_12b, gemma_27b, dolphin. Default: granite_docling"
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
    factory = ServiceFactory()
    types = [t.strip() for t in file_types.split(",")] if file_types else None
    try:
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

        if json_output:
            data = {
                "name": repo.name,
                "path": repo.path,
                "file_types": repo.file_types,
                "embedding_provider": repo.embedding_provider,
                "embedding_model": repo.embedding_model,
                "exclude_patterns": repo.exclude_patterns,
                "image_pipeline": repo.image_pipeline,
                "image_vlm_model": repo.image_vlm_model,
                "audio_asr_model": repo.audio_asr_model,
                "purged_documents": purged,
            }
            typer.echo(json.dumps(data, default=str))
        else:
            console.print(f"[green]✓[/green] Updated repository '[bold]{repo.name}[/bold]'")
            if added_patterns:
                console.print(f"  Added exclusion patterns: {', '.join(added_patterns)}")
            if purged:
                console.print(f"  Purged [bold]{purged}[/bold] previously-indexed document(s) matching new exclusions")
            elif added_patterns and not no_purge:
                console.print("  [dim]No previously-indexed documents matched the new exclusions[/dim]")
    except ValueError as e:
        if json_output:
            typer.echo(json.dumps({"error": str(e)}))
        else:
            console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@repo_app.command("list")
def list_repos(
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """List all configured repositories."""
    factory = ServiceFactory()
    repos = factory.repository_service.list_repositories()

    if json_output:
        data = {
            "repositories": [
                {
                    "name": repo.name,
                    "path": repo.path,
                    "file_types": repo.file_types,
                    "embedding_provider": repo.embedding_provider,
                    "embedding_model": repo.embedding_model,
                    "exclude_patterns": repo.exclude_patterns,
                }
                for repo in repos
            ]
        }
        typer.echo(json.dumps(data, default=str))
        return

    if not repos:
        console.print("[dim]No repositories configured.[/dim]")
        return

    table = Table(title="Repositories", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="bold")
    table.add_column("Path")
    table.add_column("File Types")
    table.add_column("Embedding Provider")
    table.add_column("Model")
    table.add_column("Exclude Patterns")

    for repo in repos:
        table.add_row(
            repo.name,
            repo.path,
            ", ".join(repo.file_types),
            repo.embedding_provider,
            repo.embedding_model or "[dim]default[/dim]",
            ", ".join(repo.exclude_patterns) if repo.exclude_patterns else "[dim]none[/dim]",
        )

    console.print(table)
