import pytest

from researcher.conftest import make_doc_result, make_search_result
from researcher.enums import SearchMode
from researcher.search_modes import SEARCH_MODES


class DescribeSearchModeCoverage:
    def should_have_an_entry_for_every_search_mode(self):
        assert set(SEARCH_MODES) == set(SearchMode)


class DescribeSearchModeSortKeys:
    def should_sort_fragments_by_distance(self):
        spec = SEARCH_MODES[SearchMode.FRAGMENTS]
        result = make_search_result(distance=0.42)

        assert spec.sort_key(result) == 0.42

    def should_sort_documents_by_best_distance(self):
        spec = SEARCH_MODES[SearchMode.DOCUMENTS]
        result = make_doc_result(best_distance=0.42)

        assert spec.sort_key(result) == 0.42


class DescribeSearchModeServiceMethods:
    @pytest.mark.parametrize(
        ("mode", "expected_method"),
        [(SearchMode.FRAGMENTS, "search_fragments"), (SearchMode.DOCUMENTS, "search_documents")],
    )
    def should_name_the_matching_search_service_method(self, mode, expected_method):
        assert SEARCH_MODES[mode].service_method == expected_method
