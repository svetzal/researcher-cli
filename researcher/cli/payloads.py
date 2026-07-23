from typing import TypedDict


class SearchEnvelope(TypedDict):
    query: str
    mode: str
    repository: str | None
    repos_searched: list[str]
    result_count: int
    results: list[dict[str, object]]
    failed_repositories: list[str]


class RepositoriesWrapper(TypedDict):
    repositories: list[dict[str, object]]


class IndexStatusWrapper(TypedDict):
    repositories: list[dict[str, object]]
