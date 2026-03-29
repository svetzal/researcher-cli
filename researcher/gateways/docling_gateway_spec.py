from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from researcher.gateways.docling_gateway import DoclingGateway


class DescribeDoclingGateway:
    @pytest.fixture
    def gateway(self):
        return DoclingGateway()

    def should_defer_converter_creation_until_first_convert(self, gateway):
        assert gateway._converter is None

        mock_document = MagicMock()
        mock_result = MagicMock()
        mock_result.document = mock_document
        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result

        with patch(
            "researcher.gateways.docling_gateway.build_document_converter",
            return_value=mock_converter,
        ) as mock_build:
            gateway.convert(Path("/fake/doc.md"))

        mock_build.assert_called_once()

    def should_reuse_converter_on_subsequent_calls(self, gateway):
        mock_document = MagicMock()
        mock_result = MagicMock()
        mock_result.document = mock_document
        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result

        with patch(
            "researcher.gateways.docling_gateway.build_document_converter",
            return_value=mock_converter,
        ) as mock_build:
            gateway.convert(Path("/fake/doc1.md"))
            gateway.convert(Path("/fake/doc2.md"))

        mock_build.assert_called_once()

    def should_defer_chunker_creation_until_first_chunk(self, gateway):
        assert gateway._chunker is None

        mock_chunker = MagicMock()
        mock_chunker.chunk.return_value = []

        with patch("docling.chunking.HybridChunker", return_value=mock_chunker):
            gateway.chunk(MagicMock())

        assert gateway._chunker is mock_chunker

    def should_return_document_from_convert_result(self, gateway):
        mock_document = MagicMock()
        mock_result = MagicMock()
        mock_result.document = mock_document
        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result

        with patch("researcher.gateways.docling_gateway.build_document_converter", return_value=mock_converter):
            result = gateway.convert(Path("/fake/doc.md"))

        assert result is mock_document

    def should_return_list_from_chunk(self, gateway):
        mock_chunks = [MagicMock(), MagicMock()]
        mock_chunker = MagicMock()
        mock_chunker.chunk.return_value = iter(mock_chunks)

        with patch("docling.chunking.HybridChunker", return_value=mock_chunker):
            result = gateway.chunk(MagicMock())

        assert isinstance(result, list)
        assert len(result) == 2
