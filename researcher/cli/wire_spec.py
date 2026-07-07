from pathlib import Path

from researcher.cli.wire import (
    DocumentWireResult,
    FragmentWireResult,
    PackEntryWire,
    PackResultWire,
    UnpackResultWire,
)
from researcher.conftest import make_doc_result, make_search_result
from researcher.model_registry import ModelCacheEntry
from researcher.services.model_archive_service import PackResult, UnpackResult


class DescribeFragmentWireResult:
    class DescribeFromDomain:
        def should_drop_fragment_id(self):
            sr = make_search_result(
                fragment_id="frag-42", doc_path="notes.md", fragment_index=1, distance=0.3, text="hello"
            )

            wire = FragmentWireResult.from_domain(sr)

            assert not hasattr(wire, "fragment_id")

        def should_project_all_expected_fields(self):
            sr = make_search_result(doc_path="/docs/auth.md", fragment_index=3, distance=0.25, text="JWT tokens")

            wire = FragmentWireResult.from_domain(sr)

            assert wire.document_path == "/docs/auth.md"
            assert wire.fragment_index == 3
            assert wire.distance == 0.25
            assert wire.text == "JWT tokens"


class DescribeDocumentWireResult:
    class DescribeFromDomain:
        def should_project_top_fragment_only(self):
            sr = make_search_result(doc_path="doc.md", fragment_index=0, distance=0.1, text="top")
            doc = make_doc_result(doc_path="doc.md", best_distance=0.1, fragment=sr)

            wire = DocumentWireResult.from_domain(doc)

            assert wire.top_fragment is not None
            assert wire.top_fragment.text == "top"
            assert wire.top_fragment.fragment_index == 0
            assert wire.top_fragment.distance == 0.1

        def should_compute_fragment_count(self):
            sr = make_search_result()
            doc = make_doc_result(fragment=sr)

            wire = DocumentWireResult.from_domain(doc)

            assert wire.fragment_count == 1

        def should_set_top_fragment_to_none_when_no_fragments(self):
            from researcher.models import DocumentSearchResult

            doc = DocumentSearchResult(document_path="empty.md", top_fragments=[], best_distance=0.9)

            wire = DocumentWireResult.from_domain(doc)

            assert wire.top_fragment is None
            assert wire.fragment_count == 0


class DescribePackEntryWire:
    class DescribeFromDomain:
        def should_map_category_and_archive_path(self):
            entry = ModelCacheEntry(
                category="docling",
                source_path=Path("/tmp/docling"),
                archive_path="docling/models",
            )

            wire = PackEntryWire.from_domain(entry)

            assert wire.category == "docling"
            assert wire.archive_path == "docling/models"


class DescribePackResultWire:
    class DescribeFromDomain:
        def should_stringify_archive_path(self):
            result = PackResult(
                archive_path=Path("/tmp/models.tar.gz"),
                entries=[],
                total_files=0,
            )

            wire = PackResultWire.from_domain(result)

            assert wire.archive == "/tmp/models.tar.gz"
            assert isinstance(wire.archive, str)

        def should_map_entries_correctly(self):
            entry = ModelCacheEntry(
                category="huggingface",
                source_path=Path("/tmp/hf"),
                archive_path="huggingface/cache",
            )
            result = PackResult(
                archive_path=Path("/tmp/models.tar.gz"),
                entries=[entry],
                total_files=5,
            )

            wire = PackResultWire.from_domain(result)

            assert wire.total_files == 5
            assert len(wire.entries) == 1
            assert wire.entries[0].category == "huggingface"
            assert wire.entries[0].archive_path == "huggingface/cache"


class DescribeUnpackResultWire:
    class DescribeFromDomain:
        def should_carry_archive_argument_as_string(self):
            result = UnpackResult(entries_restored=3, files_extracted=15)

            wire = UnpackResultWire.from_domain(Path("/tmp/archive.tar.gz"), result)

            assert wire.archive == "/tmp/archive.tar.gz"
            assert isinstance(wire.archive, str)

        def should_carry_result_fields(self):
            result = UnpackResult(entries_restored=2, files_extracted=10)

            wire = UnpackResultWire.from_domain(Path("/tmp/models.tar.gz"), result)

            assert wire.entries_restored == 2
            assert wire.files_extracted == 10
