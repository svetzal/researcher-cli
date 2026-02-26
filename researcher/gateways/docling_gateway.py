from pathlib import Path
from typing import Any

from researcher.chunking import fragments_from_chunks
from researcher.docling_config import build_converter_config
from researcher.models import Fragment


class DoclingGateway:
    """Wraps the docling library for document conversion and chunking.

    docling is imported lazily to avoid loading ML models on every CLI invocation.
    Only the `index` command needs this gateway.
    """

    def __init__(
        self,
        image_pipeline: str = "standard",
        image_vlm_model: str | None = None,
        audio_asr_model: str = "turbo",
    ):
        self._converter: Any = None
        self._chunker: Any = None
        self._converter_config = build_converter_config(image_pipeline, image_vlm_model, audio_asr_model)

    def _get_converter(self):
        if self._converter is None:
            from docling.datamodel.base_models import InputFormat
            from docling.document_converter import AudioFormatOption, DocumentConverter, ImageFormatOption

            format_options = {}
            if self._converter_config.vlm is not None:
                from docling.datamodel.pipeline_options import VlmConvertOptions, VlmPipelineOptions
                from docling.pipeline.vlm_pipeline import VlmPipeline

                vlm_opts = VlmConvertOptions.from_preset(self._converter_config.vlm.preset)
                pipeline_options = VlmPipelineOptions(vlm_options=vlm_opts)
                format_options[InputFormat.IMAGE] = ImageFormatOption(
                    pipeline_cls=VlmPipeline,
                    pipeline_options=pipeline_options,
                )

            if self._converter_config.asr is not None:
                import docling.datamodel.asr_model_specs as asr_specs
                from docling.pipeline.asr_pipeline import AsrPipeline, AsrPipelineOptions

                asr_model_spec = getattr(asr_specs, self._converter_config.asr.spec_name)
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
        return fragments_from_chunks(chunks, document_path)
