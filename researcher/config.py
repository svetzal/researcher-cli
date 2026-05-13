import dataclasses

from pydantic import BaseModel, Field


@dataclasses.dataclass
class RepoConfigOptions:
    """Optional config fields shared between add and update repository operations."""

    file_types: list[str] | None = None
    embedding_provider: str | None = None
    embedding_model: str | None = None
    image_pipeline: str | None = None
    image_vlm_model: str | None = None
    audio_asr_model: str | None = None

    def to_filtered_dict(self) -> dict:
        return {k: v for k, v in dataclasses.asdict(self).items() if v is not None}


class RepositoryConfig(BaseModel):
    """Configuration for a single document repository."""

    name: str
    path: str
    file_types: list[str] = Field(default_factory=lambda: ["md", "txt", "pdf", "docx", "html"])
    embedding_provider: str = "chromadb"  # "chromadb" | "ollama" | "openai"
    embedding_model: str | None = None
    exclude_patterns: list[str] = Field(default_factory=lambda: [".*"])
    image_pipeline: str = "standard"  # "standard" (OCR) | "vlm" (Vision Language Model)
    image_vlm_model: str | None = None  # VLM preset name; None means "granite_docling"
    audio_asr_model: str = "turbo"  # tiny | base | small | medium | large | turbo


class ResearcherConfig(BaseModel):
    """Top-level configuration for the researcher tool."""

    repositories: list[RepositoryConfig] = Field(default_factory=list)
    default_embedding_provider: str = "chromadb"
    default_embedding_model: str | None = None
    mcp_port: int = 8392
