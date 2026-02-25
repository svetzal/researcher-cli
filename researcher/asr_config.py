"""ASR and VLM model configuration and resolution for docling integration."""

ASR_MODEL_MAP: dict[str, str] = {
    "tiny": "WHISPER_TINY",
    "base": "WHISPER_BASE",
    "small": "WHISPER_SMALL",
    "medium": "WHISPER_MEDIUM",
    "large": "WHISPER_LARGE",
    "turbo": "WHISPER_TURBO",
}

DEFAULT_VLM_PRESET = "granite_docling"


def resolve_asr_spec_name(model_name: str) -> str:
    """Map a user-facing model name to the docling ASR spec constant name.

    Args:
        model_name: User-facing model name (e.g., "tiny", "base", "turbo").

    Returns:
        The docling ASR spec constant name (e.g., "WHISPER_TINY").
        Defaults to "WHISPER_TURBO" if the name is unrecognized.
    """
    return ASR_MODEL_MAP.get(model_name, "WHISPER_TURBO")


def resolve_vlm_preset(image_vlm_model: str | None) -> str:
    """Resolve the VLM model preset name.

    Args:
        image_vlm_model: The user-specified VLM model name, or None for default.

    Returns:
        The VLM preset name to use.
    """
    return image_vlm_model or DEFAULT_VLM_PRESET
