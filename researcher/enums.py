"""Closed-set domain value enums for researcher-cli configuration."""

import enum


class EmbeddingProvider(enum.StrEnum):
    CHROMADB = "chromadb"
    OLLAMA = "ollama"
    OPENAI = "openai"


class ImagePipeline(enum.StrEnum):
    STANDARD = "standard"
    VLM = "vlm"


class AudioAsrModel(enum.StrEnum):
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    TURBO = "turbo"


class SearchMode(enum.StrEnum):
    FRAGMENTS = "fragments"
    DOCUMENTS = "documents"
