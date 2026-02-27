from unittest.mock import Mock

from researcher.chunking import chunk_plain_text, fragments_from_chunks
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


class DescribeChunkPlainText:
    def should_return_empty_list_for_empty_text(self):
        assert chunk_plain_text("", "/doc.txt") == []

    def should_return_empty_list_for_whitespace_only(self):
        assert chunk_plain_text("   \n\n  ", "/doc.txt") == []

    def should_return_single_fragment_for_short_text(self):
        result = chunk_plain_text("Hello world", "/doc.txt")

        assert len(result) == 1
        assert result[0].text == "Hello world"
        assert result[0].document_path == "/doc.txt"
        assert result[0].fragment_index == 0

    def should_split_on_paragraph_boundaries(self):
        para_a = "A" * 600
        para_b = "B" * 600
        text = f"{para_a}\n\n{para_b}"

        result = chunk_plain_text(text, "/doc.txt", max_chars=1000, overlap_chars=200)

        assert len(result) == 2
        assert result[0].text == para_a
        assert para_b in result[1].text

    def should_include_overlap_between_chunks(self):
        para1 = "A" * 400
        para2 = "B" * 400
        para3 = "C" * 400

        result = chunk_plain_text(
            f"{para1}\n\n{para2}\n\n{para3}",
            "/doc.txt",
            max_chars=900,
            overlap_chars=500,
        )

        assert len(result) == 2
        # Second chunk should contain para2 (overlap) and para3
        assert para2 in result[1].text
        assert para3 in result[1].text

    def should_skip_empty_paragraphs(self):
        text = "Hello\n\n\n\nWorld"

        result = chunk_plain_text(text, "/doc.txt")

        assert len(result) == 1
        assert result[0].text == "Hello\n\nWorld"

    def should_assign_sequential_fragment_indices(self):
        paras = [f"Paragraph {i} " + "x" * 500 for i in range(5)]
        text = "\n\n".join(paras)

        result = chunk_plain_text(text, "/doc.txt", max_chars=600, overlap_chars=100)

        indices = [f.fragment_index for f in result]
        assert indices == list(range(len(result)))

    def should_set_document_path_on_all_fragments(self):
        paras = ["A" * 600, "B" * 600]
        text = "\n\n".join(paras)

        result = chunk_plain_text(text, "/my/doc.txt", max_chars=1000, overlap_chars=200)

        assert all(f.document_path == "/my/doc.txt" for f in result)
