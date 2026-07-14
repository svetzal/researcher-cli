"""Embedding provider configuration resolution for EmbeddingGateway."""

from pydantic import BaseModel, ConfigDict

from researcher.enums import EmbeddingProvider

# Default embedding model for each provider
_DEFAULT_MODELS: dict[EmbeddingProvider, str] = {
    EmbeddingProvider.CHROMADB: "default",
    EmbeddingProvider.OLLAMA: "nomic-embed-text",
    EmbeddingProvider.OPENAI: "text-embedding-3-small",
}

# Providers that honour a model override
_OVERRIDABLE: set[EmbeddingProvider] = {EmbeddingProvider.OLLAMA, EmbeddingProvider.OPENAI}


class EmbeddingProviderConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    provider: EmbeddingProvider
    model: str


def resolve_embedding_config(provider: EmbeddingProvider, model: str | None) -> EmbeddingProviderConfig:
    """Resolve the embedding provider configuration.

    Args:
        provider: The embedding provider to use.
        model: An optional model override. Falls back to a provider-specific default.
               ChromaDB ignores the model override; its model is always "default".

    Returns:
        A fully resolved EmbeddingProviderConfig.
    """
    default_model = _DEFAULT_MODELS[provider]
    resolved_model = model if (model and provider in _OVERRIDABLE) else default_model
    return EmbeddingProviderConfig(provider=provider, model=resolved_model)
