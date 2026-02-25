from unittest.mock import Mock

from researcher.chunking import fragments_from_chunks
from researcher.models import Fragment


class DescribeFragmentsFromChunks:
    def should_convert_chunks_with_text_attribute(self):
        chunk = Mock()
        chunk.text = "Hello world"

        result = fragments_from_chunks([chunk], "/doc.md")

        assert result == [Fragment(text="Hello world", document_path="/doc.md", fragment_index=0)]

    def should_strip_whitespace_from_chunk_text(self):
        chunk = Mock()
        chunk.text = "  padded text  "

        result = fragments_from_chunks([chunk], "/doc.md")

        assert result[0].text == "padded text"

    def should_filter_empty_chunks(self):
        empty_chunk = Mock()
        empty_chunk.text = "   "
        valid_chunk = Mock()
        valid_chunk.text = "content"

        result = fragments_from_chunks([empty_chunk, valid_chunk], "/doc.md")

        assert len(result) == 1
        assert result[0].text == "content"

    def should_preserve_original_index_for_fragment_index(self):
        empty_chunk = Mock()
        empty_chunk.text = ""
        valid_chunk = Mock()
        valid_chunk.text = "content"

        result = fragments_from_chunks([empty_chunk, valid_chunk], "/doc.md")

        assert result[0].fragment_index == 1

    def should_fall_back_to_str_conversion_when_no_text_attribute(self):
        chunk = "plain string chunk"

        result = fragments_from_chunks([chunk], "/doc.md")

        assert result[0].text == "plain string chunk"

    def should_return_empty_list_for_empty_input(self):
        result = fragments_from_chunks([], "/doc.md")

        assert result == []

    def should_handle_multiple_chunks(self):
        chunks = [Mock(text="first"), Mock(text="second"), Mock(text="third")]

        result = fragments_from_chunks(chunks, "/doc.md")

        assert len(result) == 3
        assert [f.text for f in result] == ["first", "second", "third"]
        assert [f.fragment_index for f in result] == [0, 1, 2]

    def should_set_document_path_on_all_fragments(self):
        chunks = [Mock(text="a"), Mock(text="b")]

        result = fragments_from_chunks(chunks, "/path/to/doc.md")

        assert all(f.document_path == "/path/to/doc.md" for f in result)
