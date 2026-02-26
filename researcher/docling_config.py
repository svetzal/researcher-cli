"""Docling converter configuration resolution for DoclingGateway."""

from pydantic import BaseModel, ConfigDict

from researcher.asr_config import resolve_asr_spec_name, resolve_vlm_preset


class VlmFormatConfig(BaseModel):
    """Configuration for the VLM image processing pipeline."""

    model_config = ConfigDict(frozen=True)

    preset: str


class AsrFormatConfig(BaseModel):
    """Configuration for the ASR audio processing pipeline."""

    model_config = ConfigDict(frozen=True)

    spec_name: str


class ConverterConfig(BaseModel):
    """Resolved configuration for the Docling DocumentConverter."""

    model_config = ConfigDict(frozen=True)

    vlm: VlmFormatConfig | None
    asr: AsrFormatConfig | None


def build_converter_config(
    image_pipeline: str,
    image_vlm_model: str | None,
    audio_asr_model: str,
) -> ConverterConfig:
    """Build a ConverterConfig from user-facing parameters.

    Args:
        image_pipeline: The image processing pipeline to use ("vlm" or "standard").
        image_vlm_model: An optional VLM model override. Falls back to default preset.
        audio_asr_model: The ASR model name for audio transcription. Empty string disables ASR.

    Returns:
        A fully resolved ConverterConfig.
    """
    vlm = None
    if image_pipeline == "vlm":
        vlm = VlmFormatConfig(preset=resolve_vlm_preset(image_vlm_model))

    asr = None
    if audio_asr_model:
        asr = AsrFormatConfig(spec_name=resolve_asr_spec_name(audio_asr_model))

    return ConverterConfig(vlm=vlm, asr=asr)
