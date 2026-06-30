"""ASR model configuration and resolution for docling integration."""

from researcher.enums import AudioAsrModel
from researcher.platform import is_apple_silicon

ASR_MODEL_MAP: dict[str, str] = {
    "tiny": "WHISPER_TINY",
    "base": "WHISPER_BASE",
    "small": "WHISPER_SMALL",
    "medium": "WHISPER_MEDIUM",
    "large": "WHISPER_LARGE",
    "turbo": "WHISPER_TURBO",
}

ASR_MODEL_MAP_MLX: dict[str, str] = {
    "tiny": "WHISPER_TINY_MLX",
    "base": "WHISPER_BASE_MLX",
    "small": "WHISPER_SMALL_MLX",
    "medium": "WHISPER_MEDIUM_MLX",
    "large": "WHISPER_LARGE_MLX",
    "turbo": "WHISPER_TURBO_MLX",
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
    model_map = ASR_MODEL_MAP_MLX if apple_silicon else ASR_MODEL_MAP
    return model_map[model_name]
