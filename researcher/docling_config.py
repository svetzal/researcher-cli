"""Docling converter configuration resolution for DoclingGateway."""

from typing import Any

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


def build_document_converter(config: ConverterConfig) -> Any:
    """Build a DocumentConverter from a ConverterConfig.

    All docling imports happen inside this function so they are loaded lazily.

    Args:
        config: The resolved converter configuration.

    Returns:
        A configured DocumentConverter instance.
    """
    from docling.datamodel.base_models import InputFormat
    from docling.document_converter import AudioFormatOption, DocumentConverter, ImageFormatOption

    format_options = {}
    if config.vlm is not None:
        from docling.datamodel.pipeline_options import VlmConvertOptions, VlmPipelineOptions
        from docling.pipeline.vlm_pipeline import VlmPipeline

        vlm_opts = VlmConvertOptions.from_preset(config.vlm.preset)
        pipeline_options = VlmPipelineOptions(vlm_options=vlm_opts)
        format_options[InputFormat.IMAGE] = ImageFormatOption(
            pipeline_cls=VlmPipeline,
            pipeline_options=pipeline_options,
        )

    if config.asr is not None:
        import docling.datamodel.asr_model_specs as asr_specs
        from docling.pipeline.asr_pipeline import AsrPipeline, AsrPipelineOptions

        asr_model_spec = getattr(asr_specs, config.asr.spec_name)
        asr_pipeline_options = AsrPipelineOptions(asr_options=asr_model_spec)
        format_options[InputFormat.AUDIO] = AudioFormatOption(
            pipeline_cls=AsrPipeline,
            pipeline_options=asr_pipeline_options,
        )

    return DocumentConverter(format_options=format_options if format_options else None)


def build_converter_config(
    image_pipeline: str,
    image_vlm_model: str | None,
    audio_asr_model: str,
    *,
    apple_silicon: bool | None = None,
) -> ConverterConfig:
    """Build a ConverterConfig from user-facing parameters.

    Args:
        image_pipeline: The image processing pipeline to use ("vlm" or "standard").
        image_vlm_model: An optional VLM model override. Falls back to default preset.
        audio_asr_model: The ASR model name for audio transcription. Empty string disables ASR.
        apple_silicon: Override platform detection. If None, detects automatically.

    Returns:
        A fully resolved ConverterConfig.
    """
    vlm = None
    if image_pipeline == "vlm":
        vlm = VlmFormatConfig(preset=resolve_vlm_preset(image_vlm_model))

    asr = None
    if audio_asr_model:
        asr = AsrFormatConfig(spec_name=resolve_asr_spec_name(audio_asr_model, apple_silicon=apple_silicon))

    return ConverterConfig(vlm=vlm, asr=asr)
