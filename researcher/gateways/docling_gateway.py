from collections.abc import Callable
from pathlib import Path
from typing import Any

from researcher.docling_config import build_converter_config, build_document_converter
from researcher.exceptions import DocumentConversionError
from researcher.gateways.error_wrapper import wrap_gateway_error

_wrap_docling_error = wrap_gateway_error(DocumentConversionError)


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
        converter: Any = None,
        chunker: Any = None,
    ):
        self._converter = converter
        self._chunker = chunker
        self._converter_config = (
            build_converter_config(image_pipeline, image_vlm_model, audio_asr_model) if converter is None else None
        )

    def _lazy_init(self, attr_name: str, subject: str, factory: Callable[[], Any]) -> Any:
        if getattr(self, attr_name) is None:
            try:
                setattr(self, attr_name, factory())
            except ImportError as e:
                raise DocumentConversionError(
                    f"docling is not installed. Install the 'docling' optional dependency to {subject}."
                ) from e
            except Exception as e:
                raise DocumentConversionError(f"Failed to initialize docling {subject}: {e}") from e
        return getattr(self, attr_name)

    def _get_converter(self):
        return self._lazy_init(
            "_converter", "convert non-text documents", lambda: build_document_converter(self._converter_config)
        )

    def _get_chunker(self):
        def _make_chunker():
            from docling.chunking import HybridChunker

            return HybridChunker()

        return self._lazy_init("_chunker", "chunk documents", _make_chunker)

    @_wrap_docling_error("Failed to convert '{file_path}': {e}")
    def convert(self, file_path: Path) -> Any:
        converter = self._get_converter()
        result = converter.convert(str(file_path))
        return result.document

    @_wrap_docling_error("Failed to chunk document: {e}")
    def chunk(self, document: Any) -> list[Any]:
        chunker = self._get_chunker()
        return list(chunker.chunk(document))
