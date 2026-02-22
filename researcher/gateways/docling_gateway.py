from pathlib import Path
from typing import Any

from researcher.models import Fragment


class DoclingGateway:
    """Wraps the docling library for document conversion and chunking.

    docling is imported lazily to avoid loading ML models on every CLI invocation.
    Only the `index` command needs this gateway.
    """

    _ASR_MODEL_MAP: dict[str, str] = {
        "tiny": "WHISPER_TINY",
        "base": "WHISPER_BASE",
        "small": "WHISPER_SMALL",
        "medium": "WHISPER_MEDIUM",
        "large": "WHISPER_LARGE",
        "turbo": "WHISPER_TURBO",
    }

    def __init__(
        self,
        image_pipeline: str = "standard",
        image_vlm_model: str | None = None,
        audio_asr_model: str = "turbo",
    ):
        self._converter: Any = None
        self._chunker: Any = None
        self._image_pipeline = image_pipeline
        self._image_vlm_model = image_vlm_model
        self._audio_asr_model = audio_asr_model

    def _get_converter(self):
        if self._converter is None:
            from docling.datamodel.base_models import InputFormat
            from docling.document_converter import AudioFormatOption, DocumentConverter, ImageFormatOption

            format_options = {}
            if self._image_pipeline == "vlm":
                from docling.datamodel.pipeline_options import VlmConvertOptions, VlmPipelineOptions
                from docling.pipeline.vlm_pipeline import VlmPipeline

                vlm_opts = VlmConvertOptions.from_preset(self._image_vlm_model or "granite_docling")
                pipeline_options = VlmPipelineOptions(vlm_options=vlm_opts)
                format_options[InputFormat.IMAGE] = ImageFormatOption(
                    pipeline_cls=VlmPipeline,
                    pipeline_options=pipeline_options,
                )

            if self._audio_asr_model:
                import docling.datamodel.asr_model_specs as asr_specs
                from docling.pipeline.asr_pipeline import AsrPipeline, AsrPipelineOptions

                spec_name = self._ASR_MODEL_MAP.get(self._audio_asr_model, "WHISPER_TURBO")
                asr_model_spec = getattr(asr_specs, spec_name)
                asr_pipeline_options = AsrPipelineOptions(asr_options=asr_model_spec)
                format_options[InputFormat.AUDIO] = AudioFormatOption(
                    pipeline_cls=AsrPipeline,
                    pipeline_options=asr_pipeline_options,
                )

            self._converter = DocumentConverter(format_options=format_options if format_options else None)
        return self._converter

    def _get_chunker(self):
        if self._chunker is None:
            from docling.chunking import HybridChunker

            self._chunker = HybridChunker()
        return self._chunker

    def convert(self, file_path: Path) -> Any:
        """Convert a document file to a DoclingDocument."""
        converter = self._get_converter()
        result = converter.convert(str(file_path))
        return result.document

    def chunk(self, document: Any, document_path: str) -> list[Fragment]:
        """Chunk a DoclingDocument into text fragments."""
        chunker = self._get_chunker()
        chunks = list(chunker.chunk(document))
        fragments = []
        for i, chunk in enumerate(chunks):
            text = chunk.text.strip() if hasattr(chunk, "text") else str(chunk).strip()
            if not text:
                continue
            fragments.append(
                Fragment(
                    text=text,
                    document_path=document_path,
                    fragment_index=i,
                )
            )
        return fragments
