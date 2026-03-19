"""ASR and VLM model configuration and resolution for docling integration."""

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

DEFAULT_VLM_PRESET = "granite_docling"


def resolve_asr_spec_name(model_name: str) -> str:
    """Map a user-facing model name to the docling ASR spec constant name.

    On Apple Silicon, selects the MLX variant for GPU acceleration.
    On other platforms, selects the standard openai-whisper variant.

    Args:
        model_name: User-facing model name (e.g., "tiny", "base", "turbo").

    Returns:
        The docling ASR spec constant name (e.g., "WHISPER_TURBO" or "WHISPER_TURBO_MLX").
        Defaults to the turbo variant if the name is unrecognized.
    """
    model_map = ASR_MODEL_MAP_MLX if is_apple_silicon() else ASR_MODEL_MAP
    default = "WHISPER_TURBO_MLX" if is_apple_silicon() else "WHISPER_TURBO"
    return model_map.get(model_name, default)


def resolve_vlm_preset(image_vlm_model: str | None) -> str:
    """Resolve the VLM model preset name.

    Args:
        image_vlm_model: The user-specified VLM model name, or None for default.

    Returns:
        The VLM preset name to use.
    """
    return image_vlm_model or DEFAULT_VLM_PRESET
