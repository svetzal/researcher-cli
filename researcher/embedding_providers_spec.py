import pytest
from pydantic import ValidationError

from researcher.embedding_providers import EmbeddingProviderConfig, resolve_embedding_config
from researcher.enums import EmbeddingProvider


class DescribeEmbeddingProviderConfig:
    def should_reject_invalid_provider(self):
        with pytest.raises(ValidationError):
            EmbeddingProviderConfig(provider="bogus", model="x")


class DescribeResolveEmbeddingConfig:
    def should_resolve_chromadb_with_default_model(self):
        result = resolve_embedding_config("chromadb", None)

        assert result == EmbeddingProviderConfig(provider="chromadb", model="default")

    def should_resolve_ollama_with_default_model(self):
        result = resolve_embedding_config("ollama", None)

        assert result == EmbeddingProviderConfig(provider="ollama", model="nomic-embed-text")

    def should_resolve_ollama_with_custom_model(self):
        result = resolve_embedding_config("ollama", "mxbai-embed-large")

        assert result == EmbeddingProviderConfig(provider="ollama", model="mxbai-embed-large")

    def should_resolve_openai_with_default_model(self):
        result = resolve_embedding_config("openai", None)

        assert result == EmbeddingProviderConfig(provider="openai", model="text-embedding-3-small")

    def should_resolve_openai_with_custom_model(self):
        result = resolve_embedding_config("openai", "text-embedding-3-large")

        assert result == EmbeddingProviderConfig(provider="openai", model="text-embedding-3-large")

    @pytest.mark.parametrize("provider", list(EmbeddingProvider))
    def should_return_non_empty_model_for_every_provider(self, provider):
        result = resolve_embedding_config(provider, None)

        assert result.model
