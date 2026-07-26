"""Single source of truth for what differs between fragment-mode and document-mode search.

Every layer that needs to branch on ``SearchMode`` (the multi-repo search service, the
MCP tool defaults) reads from this table instead of restating the fragments/documents
dichotomy with its own ``if mode == ...`` dispatch.

This module intentionally imports only ``enums`` and ``models`` — no CLI, no MCP —
so the service layer can depend on it without pulling in presentation concerns.
"""

from collections.abc import Callable

from pydantic import BaseModel, ConfigDict

from researcher.enums import SearchMode


class SearchModeSpec(BaseModel):
    model_config = ConfigDict(frozen=True)

    service_method: str
    sort_key: Callable[[object], float]
    default_n_results: int


SEARCH_MODES: dict[SearchMode, SearchModeSpec] = {
    SearchMode.FRAGMENTS: SearchModeSpec(
        service_method="search_fragments",
        sort_key=lambda r: r.distance,
        default_n_results=10,
    ),
    SearchMode.DOCUMENTS: SearchModeSpec(
        service_method="search_documents",
        sort_key=lambda r: r.best_distance,
        default_n_results=5,
    ),
}
