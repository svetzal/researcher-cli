import logging
from functools import cached_property
from pathlib import Path

from researcher.config import RepositoryConfig, ResearcherConfig
from researcher.embedding_providers import resolve_embedding_config
from researcher.gateways.checksum_gateway import ChecksumGateway
from researcher.gateways.chroma_gateway import ChromaGateway
from researcher.gateways.chromadb_embedding_gateway import ChromaDbEmbeddingGateway
from researcher.gateways.config_gateway import DEFAULT_CONFIG_DIR, ConfigGateway
from researcher.gateways.docling_gateway import DoclingGateway
from researcher.gateways.embedding_gateway import EmbeddingGateway
from researcher.gateways.filesystem_gateway import FilesystemGateway
from researcher.gateways.model_cache_gateway import ModelCacheGateway
from researcher.gateways.ollama_embedding_gateway import OllamaEmbeddingGateway
from researcher.gateways.openai_embedding_gateway import OpenAIEmbeddingGateway
from researcher.services.index_service import IndexService
from researcher.services.model_archive_service import ModelArchiveService
from researcher.services.repository_service import RepositoryService
from researcher.services.search_service import SearchService


class ServiceFactory:
    """Composition root — wires all service and gateway dependencies."""

    def __init__(self, config_dir: Path | None = None):
        self._config_dir = config_dir or DEFAULT_CONFIG_DIR

    @cached_property
    def config_gateway(self) -> ConfigGateway:
        return ConfigGateway(config_dir=self._config_dir)

    @cached_property
    def config(self) -> ResearcherConfig:
        return self.config_gateway.load()

    @cached_property
    def repository_service(self) -> RepositoryService:
        return RepositoryService(config_gateway=self.config_gateway)

    @cached_property
    def _docling_available(self) -> bool:
        """Check whether the docling library can be imported."""
        try:
            import docling.document_converter  # noqa: F401

            return True
        except Exception:
            logging.getLogger(__name__).warning(
                "docling unavailable — only plain text files (.md, .txt) will be indexed"
            )
            return False

    def _create_embedding_gateway(self, repo: RepositoryConfig) -> EmbeddingGateway:
        config = resolve_embedding_config(repo.embedding_provider, repo.embedding_model)
        match config.provider:
            case "chromadb":
                return ChromaDbEmbeddingGateway()
            case "ollama":
                return OllamaEmbeddingGateway(model=config.model)
            case "openai":
                return OpenAIEmbeddingGateway(model=config.model)
            case _:
                raise ValueError(f"Unsupported embedding provider: {config.provider}")

    def _repo_data_dir(self, repo: RepositoryConfig) -> Path:
        """Return the data directory for a repository."""
        return self._config_dir / "repositories" / repo.name

    def index_service(self, repo: RepositoryConfig) -> IndexService:
        """Create a fresh IndexService for the given repository."""
        repo_data_dir = self._repo_data_dir(repo)
        chroma_dir = repo_data_dir / "chroma"
        checksums_path = repo_data_dir / "checksums.json"

        docling_gw: DoclingGateway | None = None
        if self._docling_available:
            docling_gw = DoclingGateway(
                image_pipeline=repo.image_pipeline,
                image_vlm_model=repo.image_vlm_model,
                audio_asr_model=repo.audio_asr_model,
            )

        return IndexService(
            filesystem_gateway=FilesystemGateway(base_path=Path(repo.path)),
            docling_gateway=docling_gw,
            embedding_gateway=self._create_embedding_gateway(repo),
            chroma_gateway=ChromaGateway(persist_directory=chroma_dir),
            repo_name=repo.name,
            checksum_gateway=ChecksumGateway(checksums_path=checksums_path),
        )

    def model_archive_service(self) -> ModelArchiveService:
        """Create a ModelArchiveService."""
        return ModelArchiveService(model_cache_gateway=ModelCacheGateway())

    def search_service(self, repo: RepositoryConfig) -> SearchService:
        """Create a fresh SearchService for the given repository."""
        chroma_dir = self._repo_data_dir(repo) / "chroma"

        return SearchService(
            chroma_gateway=ChromaGateway(persist_directory=chroma_dir),
            embedding_gateway=self._create_embedding_gateway(repo),
        )
