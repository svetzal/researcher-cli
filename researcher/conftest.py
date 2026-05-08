from unittest.mock import Mock

import pytest

from researcher.config import RepositoryConfig
from researcher.models import DocumentSearchResult, SearchResult
from researcher.service_factory import ServiceFactory


@pytest.fixture
def mock_factory():
    return Mock(spec=ServiceFactory)


def make_repo(name: str = "repo", path: str | None = None) -> RepositoryConfig:
    return RepositoryConfig(name=name, path=path or f"/tmp/{name}")


def make_search_result(
    fragment_id: str = "f1",
    doc_path: str = "doc.md",
    fragment_index: int = 0,
    distance: float = 0.15,
    text: str = "some text",
) -> SearchResult:
    return SearchResult(
        fragment_id=fragment_id,
        text=text,
        document_path=doc_path,
        fragment_index=fragment_index,
        distance=distance,
    )


def make_doc_result(
    doc_path: str = "doc.md",
    best_distance: float = 0.15,
    fragment: SearchResult | None = None,
) -> DocumentSearchResult:
    fr = fragment or make_search_result(doc_path=doc_path, distance=best_distance)
    return DocumentSearchResult(document_path=doc_path, top_fragments=[fr], best_distance=best_distance)
