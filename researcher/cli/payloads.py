from typing import TypedDict


class IndexResultPayload(TypedDict):
    repository: str
    documents_indexed: int
    documents_skipped: int
    documents_failed: int
    documents_purged: int
    fragments_created: int
    errors: list[str]


class IndexStatsPayload(TypedDict):
    repository_name: str
    total_documents: int
    total_fragments: int
    last_indexed: str | None


class FragmentResultPayload(TypedDict):
    document_path: str
    fragment_index: int
    distance: float
    text: str


class TopFragmentPayload(TypedDict):
    text: str
    fragment_index: int
    distance: float


class DocumentSearchResultPayload(TypedDict):
    document_path: str
    best_distance: float
    fragment_count: int
    top_fragment: TopFragmentPayload | None


class SearchEnvelope(TypedDict):
    query: str
    mode: str
    repository: str | None
    repos_searched: list[str]
    result_count: int
    results: list[FragmentResultPayload] | list[DocumentSearchResultPayload]


class PackEntryPayload(TypedDict):
    category: str
    archive_path: str


class PackResultPayload(TypedDict):
    archive: str
    total_files: int
    entries: list[PackEntryPayload]


class UnpackResultPayload(TypedDict):
    archive: str
    entries_restored: int
    files_extracted: int


class RepositoriesWrapper(TypedDict):
    repositories: list[IndexResultPayload]


class IndexStatusWrapper(TypedDict):
    repositories: list[IndexStatsPayload]
