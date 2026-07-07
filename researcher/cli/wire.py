from pathlib import Path

from pydantic import BaseModel, ConfigDict

from researcher.model_registry import ModelCacheEntry
from researcher.models import DocumentSearchResult, SearchResult
from researcher.services.model_archive_service import PackResult, UnpackResult


class FragmentWireResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    document_path: str
    fragment_index: int
    text: str
    distance: float

    @classmethod
    def from_domain(cls, result: SearchResult) -> "FragmentWireResult":
        return cls(
            document_path=result.document_path,
            fragment_index=result.fragment_index,
            text=result.text,
            distance=result.distance,
        )


class TopFragmentWire(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str
    fragment_index: int
    distance: float

    @classmethod
    def from_domain(cls, tf: SearchResult) -> "TopFragmentWire":
        return cls(text=tf.text, fragment_index=tf.fragment_index, distance=tf.distance)


class DocumentWireResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    document_path: str
    best_distance: float
    fragment_count: int
    top_fragment: TopFragmentWire | None

    @classmethod
    def from_domain(cls, result: DocumentSearchResult) -> "DocumentWireResult":
        top = result.top_fragment
        return cls(
            document_path=result.document_path,
            best_distance=result.best_distance,
            fragment_count=result.fragment_count,
            top_fragment=TopFragmentWire.from_domain(top) if top else None,
        )


class PackEntryWire(BaseModel):
    model_config = ConfigDict(frozen=True)

    category: str
    archive_path: str

    @classmethod
    def from_domain(cls, entry: ModelCacheEntry) -> "PackEntryWire":
        return cls(category=entry.category, archive_path=entry.archive_path)


class PackResultWire(BaseModel):
    model_config = ConfigDict(frozen=True)

    archive: str
    total_files: int
    entries: list[PackEntryWire]

    @classmethod
    def from_domain(cls, result: PackResult) -> "PackResultWire":
        return cls(
            archive=str(result.archive_path),
            total_files=result.total_files,
            entries=[PackEntryWire.from_domain(e) for e in result.entries],
        )


class UnpackResultWire(BaseModel):
    model_config = ConfigDict(frozen=True)

    archive: str
    entries_restored: int
    files_extracted: int

    @classmethod
    def from_domain(cls, archive: Path, result: UnpackResult) -> "UnpackResultWire":
        return cls(
            archive=str(archive),
            entries_restored=result.entries_restored,
            files_extracted=result.files_extracted,
        )
