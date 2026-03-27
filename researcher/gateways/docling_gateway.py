from pathlib import Path
from typing import Any

from researcher.docling_config import build_converter_config, build_document_converter


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
            self._converter = build_document_converter(self._converter_config)
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

    def chunk(self, document: Any) -> list[Any]:
        """Chunk a DoclingDocument into raw chunks."""
        chunker = self._get_chunker()
        return list(chunker.chunk(document))
