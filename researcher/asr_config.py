"""ASR model configuration and resolution for docling integration."""

from pydantic import BaseModel, ConfigDict

from researcher.enums import AudioAsrModel
from researcher.platform import is_apple_silicon


class AsrModelSpec(BaseModel):
    """Single source of truth for one ASR model's identifiers across every consumer.

    ``spec_name`` / ``mlx_spec_name`` are the docling ASR spec constant names.
    ``mlx_repo_id`` is the HuggingFace repo ID used to cache the MLX variant on
    Apple Silicon. ``whisper_cache_file`` is the openai-whisper cache filename
    used on non-Apple platforms.
    """

    model_config = ConfigDict(frozen=True)

    spec_name: str
    mlx_spec_name: str
    mlx_repo_id: str
    whisper_cache_file: str


ASR_MODELS: dict[AudioAsrModel, AsrModelSpec] = {
    AudioAsrModel.TINY: AsrModelSpec(
        spec_name="WHISPER_TINY",
        mlx_spec_name="WHISPER_TINY_MLX",
        mlx_repo_id="mlx-community/whisper-tiny-mlx",
        whisper_cache_file="tiny.pt",
    ),
    AudioAsrModel.BASE: AsrModelSpec(
        spec_name="WHISPER_BASE",
        mlx_spec_name="WHISPER_BASE_MLX",
        mlx_repo_id="mlx-community/whisper-base-mlx",
        whisper_cache_file="base.pt",
    ),
    AudioAsrModel.SMALL: AsrModelSpec(
        spec_name="WHISPER_SMALL",
        mlx_spec_name="WHISPER_SMALL_MLX",
        mlx_repo_id="mlx-community/whisper-small-mlx",
        whisper_cache_file="small.pt",
    ),
    AudioAsrModel.MEDIUM: AsrModelSpec(
        spec_name="WHISPER_MEDIUM",
        mlx_spec_name="WHISPER_MEDIUM_MLX",
        mlx_repo_id="mlx-community/whisper-medium-mlx-8bit",
        whisper_cache_file="medium.pt",
    ),
    AudioAsrModel.LARGE: AsrModelSpec(
        spec_name="WHISPER_LARGE",
        mlx_spec_name="WHISPER_LARGE_MLX",
        mlx_repo_id="mlx-community/whisper-large-mlx-8bit",
        whisper_cache_file="large-v3.pt",
    ),
    AudioAsrModel.TURBO: AsrModelSpec(
        spec_name="WHISPER_TURBO",
        mlx_spec_name="WHISPER_TURBO_MLX",
        mlx_repo_id="mlx-community/whisper-turbo",
        whisper_cache_file="turbo.pt",
    ),
}


def resolve_asr_spec_name(model_name: AudioAsrModel, *, apple_silicon: bool | None = None) -> str:
    """Map a user-facing model name to the docling ASR spec constant name.

    On Apple Silicon, selects the MLX variant for GPU acceleration.
    On other platforms, selects the standard openai-whisper variant.

    Args:
        model_name: ASR model name (must be a valid AudioAsrModel member).
        apple_silicon: Override platform detection. If None, detects automatically.

    Returns:
        The docling ASR spec constant name (e.g., "WHISPER_TURBO" or "WHISPER_TURBO_MLX").
    """
    if apple_silicon is None:
        apple_silicon = is_apple_silicon()
    spec = ASR_MODELS[model_name]
    return spec.mlx_spec_name if apple_silicon else spec.spec_name
