from functools import cached_property
from pathlib import Path

from researcher.config import ConfigGateway, RepositoryConfig, ResearcherConfig
from researcher.gateways.chroma_gateway import ChromaGateway
from researcher.gateways.docling_gateway import DoclingGateway
from researcher.gateways.embedding_gateway import EmbeddingGateway
from researcher.gateways.filesystem_gateway import FilesystemGateway
from researcher.services.index_service import IndexService
from researcher.services.repository_service import RepositoryService
from researcher.services.search_service import SearchService


class ServiceFactory:
    """Composition root — wires all service and gateway dependencies."""

    def __init__(self, config_dir: Path | None = None):
        self._config_dir = config_dir or Path.home() / ".researcher"

    @cached_property
    def config_gateway(self) -> ConfigGateway:
        return ConfigGateway(config_dir=self._config_dir)

    @cached_property
    def config(self) -> ResearcherConfig:
        return self.config_gateway.load()

    @cached_property
    def repository_service(self) -> RepositoryService:
        return RepositoryService(config_gateway=self.config_gateway)

    def index_service(self, repo: RepositoryConfig) -> IndexService:
        """Create a fresh IndexService for the given repository."""
        repo_data_dir = self._config_dir / "repositories" / repo.name
        chroma_dir = repo_data_dir / "chroma"

        return IndexService(
            filesystem_gateway=FilesystemGateway(base_path=Path(repo.path)),
            docling_gateway=DoclingGateway(
                image_pipeline=repo.image_pipeline,
                image_vlm_model=repo.image_vlm_model,
                audio_asr_model=repo.audio_asr_model,
            ),
            embedding_gateway=EmbeddingGateway(
                provider=repo.embedding_provider,
                model=repo.embedding_model,
            ),
            chroma_gateway=ChromaGateway(persist_directory=chroma_dir),
            repo_name=repo.name,
            repo_data_dir=repo_data_dir,
        )

    def search_service(self, repo: RepositoryConfig) -> SearchService:
        """Create a fresh SearchService for the given repository."""
        repo_data_dir = self._config_dir / "repositories" / repo.name
        chroma_dir = repo_data_dir / "chroma"

        return SearchService(
            chroma_gateway=ChromaGateway(persist_directory=chroma_dir),
            embedding_gateway=EmbeddingGateway(
                provider=repo.embedding_provider,
                model=repo.embedding_model,
            ),
        )
