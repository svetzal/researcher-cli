from typing import TypedDict


class SearchEnvelope(TypedDict):
    query: str
    mode: str
    repository: str | None
    repos_searched: list[str]
    result_count: int
    results: list[dict[str, object]]


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
    repositories: list[dict[str, object]]


class IndexStatusWrapper(TypedDict):
    repositories: list[dict[str, object]]
