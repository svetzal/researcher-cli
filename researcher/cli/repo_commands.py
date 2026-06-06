import typer

from researcher.cli.output import JSON_OPTION, cli_errors, cli_output, console, make_service_factory_callback
from researcher.cli.presenters import present_repo_list, present_repo_update
from researcher.config import RepoConfigOptions, RepositoryConfig
from researcher.exceptions import RepositoryAlreadyExistsError, RepositoryNotFoundError
from researcher.model_registry import API_ONLY_PRESETS, VLM_PRESET_REPOS
from researcher.service_factory import ServiceFactory

_DEFAULTS = RepositoryConfig(name="", path="")
_vlm_names = ", ".join(sorted(set(VLM_PRESET_REPOS.keys()) | API_ONLY_PRESETS))

_EMBEDDING_PROVIDER_HELP = "Embedding provider"
_EMBEDDING_MODEL_HELP = "Embedding model name"
_IMAGE_PIPELINE_HELP = "Image processing pipeline: 'standard' (OCR) or 'vlm' (Vision Language Model)"
_IMAGE_VLM_MODEL_HELP = (
    f"VLM preset name (only used when --image-pipeline=vlm). Available: {_vlm_names}. Default: granite_docling"
)
_AUDIO_ASR_MODEL_HELP = (
    "Whisper ASR model for audio files. Options: tiny, base, small, medium, large, turbo. Default: turbo"
)


def _embedding_provider_option(default: str | None) -> str:
    return typer.Option(default, "--embedding-provider", help=_EMBEDDING_PROVIDER_HELP)


def _embedding_model_option() -> str:
    return typer.Option(None, "--embedding-model", help=_EMBEDDING_MODEL_HELP)


def _image_pipeline_option(default: str | None) -> str:
    return typer.Option(default, "--image-pipeline", help=_IMAGE_PIPELINE_HELP)


def _image_vlm_model_option() -> str:
    return typer.Option(None, "--image-vlm-model", help=_IMAGE_VLM_MODEL_HELP)


def _audio_asr_model_option() -> str:
    return typer.Option(None, "--audio-asr-model", help=_AUDIO_ASR_MODEL_HELP)


repo_app = typer.Typer(help="Manage document repositories.")

make_service_factory_callback(repo_app)


@repo_app.command("add")
@cli_errors(RepositoryAlreadyExistsError)
def add_repo(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Repository name"),
    path: str = typer.Argument(..., help="Path to the document directory"),
    file_types: str = typer.Option(
        ",".join(_DEFAULTS.file_types), "--file-types", help="Comma-separated file extensions"
    ),
    embedding_provider: str = _embedding_provider_option(_DEFAULTS.embedding_provider),
    embedding_model: str = _embedding_model_option(),
    exclude: list[str] = typer.Option(
        None,
        "--exclude",
        "-e",
        help="Glob pattern to exclude (repeatable, e.g. --exclude node_modules --exclude '.*')",
    ),
    image_pipeline: str = _image_pipeline_option(_DEFAULTS.image_pipeline),
    image_vlm_model: str = _image_vlm_model_option(),
    audio_asr_model: str = _audio_asr_model_option(),
    json_output: bool = JSON_OPTION,
) -> None:
    factory: ServiceFactory = ctx.obj
    types = [t.strip() for t in file_types.split(",")]
    repo = factory.repository_service.add_repository(
        name=name,
        path=path,
        options=RepoConfigOptions(
            file_types=types,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
            image_pipeline=image_pipeline,
            image_vlm_model=image_vlm_model,
            audio_asr_model=audio_asr_model,
        ),
        exclude_patterns=exclude or [],
    )
    cli_output(
        repo.model_dump(),
        f"[green]✓[/green] Added repository '[bold]{repo.name}[/bold]' at {repo.path}",
        json_output=json_output,
    )


@repo_app.command("remove")
@cli_errors(RepositoryNotFoundError)
def remove_repo(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Repository name to remove"),
    json_output: bool = JSON_OPTION,
) -> None:
    factory: ServiceFactory = ctx.obj
    factory.repository_service.remove_repository(name)
    cli_output(
        {"name": name, "removed": True},
        f"[green]✓[/green] Removed repository '[bold]{name}[/bold]'",
        json_output=json_output,
    )


@repo_app.command("update")
@cli_errors(RepositoryNotFoundError)
def update_repo(
    ctx: typer.Context,
    name: str = typer.Argument(..., help="Repository name"),
    file_types: str = typer.Option(None, "--file-types", help="Comma-separated file extensions (replaces existing)"),
    embedding_provider: str = _embedding_provider_option(None),
    embedding_model: str = _embedding_model_option(),
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
    image_pipeline: str = _image_pipeline_option(None),
    image_vlm_model: str = _image_vlm_model_option(),
    audio_asr_model: str = _audio_asr_model_option(),
    json_output: bool = JSON_OPTION,
) -> None:
    factory: ServiceFactory = ctx.obj
    types = [t.strip() for t in file_types.split(",")] if file_types else None
    repo, added_patterns = factory.repository_service.update_repository(
        name=name,
        options=RepoConfigOptions(
            file_types=types,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model,
            image_pipeline=image_pipeline,
            image_vlm_model=image_vlm_model,
            audio_asr_model=audio_asr_model,
        ),
        add_exclude_patterns=exclude or [],
    )
    purged = 0
    if added_patterns and not no_purge:
        index_svc = factory.index_service(repo)
        purged = index_svc.purge_excluded_documents(repo)

    cli_output(
        repo.model_dump() | {"purged_documents": purged},
        lambda: present_repo_update(repo, added_patterns, purged, no_purge, console),
        json_output=json_output,
    )


@repo_app.command("list")
def list_repos(
    ctx: typer.Context,
    json_output: bool = JSON_OPTION,
) -> None:
    factory: ServiceFactory = ctx.obj
    repos = factory.repository_service.list_repositories()

    cli_output(
        {"repositories": [repo.model_dump() for repo in repos]},
        lambda: present_repo_list(repos, console),
        json_output=json_output,
    )
