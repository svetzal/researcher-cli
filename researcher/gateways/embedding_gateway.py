from typing import Any, Protocol


class EmbeddingGateway(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]


class LazyClientEmbeddingGateway(EmbeddingGateway):
    def __init__(self, model: str, client: Any = None) -> None:
        self._model = model
        self._client = client

    def _resolve_client(self) -> Any:
        return self._client if self._client is not None else self._create_client()

    def _create_client(self) -> Any:  # pragma: no cover - overridden by subclasses
        raise NotImplementedError
