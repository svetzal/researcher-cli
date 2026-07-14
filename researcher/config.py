from pydantic import BaseModel, Field

from researcher.enums import AudioAsrModel, EmbeddingProvider, ImagePipeline


class RepoConfigOptions(BaseModel):
    """Optional config fields shared between add and update repository operations."""

    file_types: list[str] | None = None
    embedding_provider: EmbeddingProvider | None = None
    embedding_model: str | None = None
    image_pipeline: ImagePipeline | None = None
    image_vlm_model: str | None = None
    audio_asr_model: AudioAsrModel | None = None


class RepositoryConfig(BaseModel):
    name: str
    path: str
    file_types: list[str] = Field(default_factory=lambda: ["md", "txt", "pdf", "docx", "html"])
    embedding_provider: EmbeddingProvider = EmbeddingProvider.CHROMADB
    embedding_model: str | None = None
    exclude_patterns: list[str] = Field(default_factory=lambda: [".*"])
    image_pipeline: ImagePipeline = ImagePipeline.STANDARD
    image_vlm_model: str | None = None
    audio_asr_model: AudioAsrModel | None = AudioAsrModel.TURBO


class ResearcherConfig(BaseModel):
    repositories: list[RepositoryConfig] = Field(default_factory=list)
    default_embedding_provider: EmbeddingProvider = EmbeddingProvider.CHROMADB
    default_embedding_model: str | None = None
    mcp_port: int = 8392
