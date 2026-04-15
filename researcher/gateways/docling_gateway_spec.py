from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from researcher.docling_config import ConverterConfig
from researcher.exceptions import DocumentConversionError
from researcher.gateways.docling_gateway import DoclingGateway

_STUB_CONFIG = ConverterConfig(vlm=None, asr=None)


@pytest.fixture
def stub_config():
    with patch(
        "researcher.gateways.docling_gateway.build_converter_config",
        return_value=_STUB_CONFIG,
    ):
        yield


class DescribeDoclingGatewayConvert:
    def should_convert_document_and_return_result(self, stub_config):
        document = MagicMock()
        mock_result = MagicMock()
        mock_result.document = document
        mock_converter = MagicMock()
        mock_converter.convert.return_value = mock_result

        with patch(
            "researcher.gateways.docling_gateway.build_document_converter",
            return_value=mock_converter,
        ):
            gateway = DoclingGateway()
            result = gateway.convert(Path("/some/file.pdf"))

        assert result is document
        mock_converter.convert.assert_called_once_with("/some/file.pdf")

    def should_raise_document_conversion_error_on_failure(self, stub_config):
        mock_converter = MagicMock()
        mock_converter.convert.side_effect = RuntimeError("parse failed")

        with patch(
            "researcher.gateways.docling_gateway.build_document_converter",
            return_value=mock_converter,
        ):
            gateway = DoclingGateway()
            with pytest.raises(DocumentConversionError, match="Failed to convert"):
                gateway.convert(Path("/bad/file.pdf"))

    def should_raise_document_conversion_error_when_docling_not_installed(self, stub_config):
        with patch(
            "researcher.gateways.docling_gateway.build_document_converter",
            side_effect=ImportError("no module named docling"),
        ):
            gateway = DoclingGateway()
            with pytest.raises(DocumentConversionError, match="docling is not installed"):
                gateway.convert(Path("/some/file.pdf"))

    def should_create_converter_only_once(self, stub_config):
        mock_converter = MagicMock()
        mock_result = MagicMock()
        mock_result.document = MagicMock()
        mock_converter.convert.return_value = mock_result

        with patch(
            "researcher.gateways.docling_gateway.build_document_converter",
            return_value=mock_converter,
        ) as mock_build:
            gateway = DoclingGateway()
            gateway.convert(Path("/file1.pdf"))
            gateway.convert(Path("/file2.pdf"))

        mock_build.assert_called_once()


class DescribeDoclingGatewayChunk:
    def should_chunk_document_into_list(self, stub_config):
        chunks = [MagicMock(), MagicMock()]
        mock_chunker = MagicMock()
        mock_chunker.chunk.return_value = iter(chunks)

        with (
            patch("researcher.gateways.docling_gateway.build_document_converter", return_value=MagicMock()),
            patch("docling.chunking.HybridChunker", return_value=mock_chunker),
        ):
            gateway = DoclingGateway()
            document = MagicMock()
            result = gateway.chunk(document)

        assert result == chunks

    def should_raise_document_conversion_error_on_chunk_failure(self, stub_config):
        mock_chunker = MagicMock()
        mock_chunker.chunk.side_effect = RuntimeError("chunking exploded")

        with (
            patch("researcher.gateways.docling_gateway.build_document_converter", return_value=MagicMock()),
            patch("docling.chunking.HybridChunker", return_value=mock_chunker),
            pytest.raises(DocumentConversionError, match="Failed to chunk"),
        ):
            gateway = DoclingGateway()
            gateway.chunk(MagicMock())
