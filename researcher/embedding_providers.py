"""Embedding provider configuration resolution for EmbeddingGateway."""

from pydantic import BaseModel, ConfigDict


class EmbeddingProviderConfig(BaseModel):
    """Resolved configuration for an embedding provider."""

    model_config = ConfigDict(frozen=True)

    provider: str
    model: str


def resolve_embedding_config(provider: str, model: str | None) -> EmbeddingProviderConfig:
    """Resolve the embedding provider configuration.

    Args:
        provider: The embedding provider name (e.g., "chromadb", "ollama", "openai").
        model: An optional model override. Falls back to a provider-specific default.

    Returns:
        A fully resolved EmbeddingProviderConfig.

    Raises:
        ValueError: If the provider is not recognized.
    """
    if provider == "chromadb":
        return EmbeddingProviderConfig(provider=provider, model="default")
    elif provider == "ollama":
        return EmbeddingProviderConfig(provider=provider, model=model or "nomic-embed-text")
    elif provider == "openai":
        return EmbeddingProviderConfig(provider=provider, model=model or "text-embedding-3-small")
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")
