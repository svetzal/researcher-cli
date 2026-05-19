from pathlib import Path
from types import SimpleNamespace

import pytest

from researcher.exceptions import DocumentConversionError
from researcher.gateways.docling_gateway import DoclingGateway


class DescribeDoclingGatewayConvert:
    def should_convert_document_and_return_result(self):
        fake_doc = object()
        fake_result = SimpleNamespace(document=fake_doc)
        fake_converter = SimpleNamespace(convert=lambda path: fake_result)
        gateway = DoclingGateway(converter=fake_converter)
        result = gateway.convert(Path("/some/file.pdf"))
        assert result is fake_doc

    def should_raise_document_conversion_error_on_failure(self):
        def failing_convert(path):
            raise RuntimeError("parse failed")

        fake_converter = SimpleNamespace(convert=failing_convert)
        gateway = DoclingGateway(converter=fake_converter)
        with pytest.raises(DocumentConversionError, match="Failed to convert"):
            gateway.convert(Path("/bad/file.pdf"))

    def should_convert_multiple_documents_correctly(self):
        docs = [object(), object()]
        results = [SimpleNamespace(document=d) for d in docs]
        calls = [0]

        def counting_convert(path):
            r = results[calls[0]]
            calls[0] += 1
            return r

        fake_converter = SimpleNamespace(convert=counting_convert)
        gateway = DoclingGateway(converter=fake_converter)
        out1 = gateway.convert(Path("/file1.pdf"))
        out2 = gateway.convert(Path("/file2.pdf"))
        assert out1 is docs[0]
        assert out2 is docs[1]


class DescribeDoclingGatewayChunk:
    def should_chunk_document_into_list(self):
        chunks = [object(), object()]
        fake_chunker = SimpleNamespace(chunk=lambda doc: iter(chunks))
        gateway = DoclingGateway(chunker=fake_chunker)
        result = gateway.chunk(object())
        assert result == chunks

    def should_raise_document_conversion_error_on_chunk_failure(self):
        def failing_chunk(doc):
            raise RuntimeError("chunking exploded")

        fake_chunker = SimpleNamespace(chunk=failing_chunk)
        gateway = DoclingGateway(chunker=fake_chunker)
        with pytest.raises(DocumentConversionError, match="Failed to chunk"):
            gateway.chunk(object())
