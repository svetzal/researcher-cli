import pytest

from researcher.chroma_parsing import collect_document_paths, parse_query_results


class DescribeParseQueryResults:
    def should_parse_single_result(self):
        raw = {
            "ids": [["f1"]],
            "documents": [["Hello world"]],
            "metadatas": [[{"document_path": "/doc.md", "fragment_index": 0}]],
            "distances": [[0.5]],
        }

        results = parse_query_results(raw)

        assert len(results) == 1
        assert results[0].fragment_id == "f1"
        assert results[0].text == "Hello world"
        assert results[0].document_path == "/doc.md"
        assert results[0].fragment_index == 0
        assert results[0].distance == 0.5

    def should_parse_multiple_results(self):
        raw = {
            "ids": [["f1", "f2"]],
            "documents": [["Hello", "World"]],
            "metadatas": [
                [
                    {"document_path": "/a.md", "fragment_index": 0},
                    {"document_path": "/b.md", "fragment_index": 1},
                ]
            ],
            "distances": [[0.1, 0.9]],
        }

        results = parse_query_results(raw)

        assert len(results) == 2
        assert results[0].fragment_id == "f1"
        assert results[1].fragment_id == "f2"

    def should_return_empty_list_for_empty_results(self):
        raw = {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

        results = parse_query_results(raw)

        assert results == []

    def should_default_document_path_when_missing(self):
        raw = {
            "ids": [["f1"]],
            "documents": [["text"]],
            "metadatas": [[{}]],
            "distances": [[0.3]],
        }

        results = parse_query_results(raw)

        assert results[0].document_path == ""
        assert results[0].fragment_index == 0

    def should_handle_missing_keys_gracefully(self):
        raw = {}

        results = parse_query_results(raw)

        assert results == []

    def should_raise_on_mismatched_list_lengths(self):
        raw = {
            "ids": [["f1", "f2"]],
            "documents": [["only one"]],
            "metadatas": [[{"document_path": "/a.md"}]],
            "distances": [[0.1]],
        }

        with pytest.raises(ValueError):
            parse_query_results(raw)


class DescribeCollectDocumentPaths:
    def should_collect_unique_paths_from_single_batch(self):
        batches = [
            [
                {"document_path": "/doc1.md"},
                {"document_path": "/doc2.md"},
                {"document_path": "/doc1.md"},
            ]
        ]

        paths = collect_document_paths(batches)

        assert paths == ["/doc1.md", "/doc2.md"]

    def should_collect_paths_across_multiple_batches(self):
        batches = [
            [{"document_path": "/doc1.md"}],
            [{"document_path": "/doc2.md"}],
            [{"document_path": "/doc1.md"}],
        ]

        paths = collect_document_paths(batches)

        assert paths == ["/doc1.md", "/doc2.md"]

    def should_return_empty_for_empty_batches(self):
        paths = collect_document_paths([])

        assert paths == []

    def should_return_empty_for_batches_with_no_paths(self):
        batches = [[{}, None, {"other_key": "value"}]]

        paths = collect_document_paths(batches)

        assert paths == []

    def should_skip_none_metadata_entries(self):
        batches = [[None, {"document_path": "/doc.md"}, None]]

        paths = collect_document_paths(batches)

        assert paths == ["/doc.md"]

    def should_return_sorted_paths(self):
        batches = [
            [
                {"document_path": "/z.md"},
                {"document_path": "/a.md"},
                {"document_path": "/m.md"},
            ]
        ]

        paths = collect_document_paths(batches)

        assert paths == ["/a.md", "/m.md", "/z.md"]
