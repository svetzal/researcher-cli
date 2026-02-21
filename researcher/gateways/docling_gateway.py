from pathlib import Path
from typing import Any

from researcher.models import Fragment


class DoclingGateway:
    """Wraps the docling library for document conversion and chunking.

    docling is imported lazily to avoid loading ML models on every CLI invocation.
    Only the `index` command needs this gateway.
    """

    def __init__(self):
        self._converter: Any = None
        self._chunker: Any = None

    def _get_converter(self):
        if self._converter is None:
            from docling.document_converter import DocumentConverter

            self._converter = DocumentConverter()
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
