from pydantic import BaseModel, ConfigDict

from researcher.models import DocumentSearchResult, SearchResult


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
