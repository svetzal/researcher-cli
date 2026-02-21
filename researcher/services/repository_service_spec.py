import tempfile
from pathlib import Path

import pytest

from researcher.config import ConfigGateway
from researcher.services.repository_service import RepositoryService


class DescribeRepositoryService:
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    @pytest.fixture
    def config_gateway(self, temp_dir):
        return ConfigGateway(config_dir=temp_dir)

    @pytest.fixture
    def service(self, config_gateway):
        return RepositoryService(config_gateway=config_gateway)

    def should_add_a_repository(self, service):
        repo = service.add_repository("my-repo", "/tmp/docs")

        assert repo.name == "my-repo"
        assert repo.path == "/tmp/docs"

    def should_persist_added_repository(self, service, config_gateway):
        service.add_repository("my-repo", "/tmp/docs")

        repos = service.list_repositories()

        assert len(repos) == 1
        assert repos[0].name == "my-repo"

    def should_raise_when_adding_duplicate_name(self, service):
        service.add_repository("my-repo", "/tmp/docs")

        with pytest.raises(ValueError, match="already exists"):
            service.add_repository("my-repo", "/tmp/other")

    def should_remove_a_repository(self, service):
        service.add_repository("my-repo", "/tmp/docs")

        service.remove_repository("my-repo")

        repos = service.list_repositories()
        assert len(repos) == 0

    def should_raise_when_removing_nonexistent_repository(self, service):
        with pytest.raises(ValueError, match="not found"):
            service.remove_repository("nonexistent")

    def should_list_all_repositories(self, service):
        service.add_repository("repo1", "/tmp/docs1")
        service.add_repository("repo2", "/tmp/docs2")

        repos = service.list_repositories()

        assert len(repos) == 2

    def should_get_repository_by_name(self, service):
        service.add_repository("my-repo", "/tmp/docs")

        repo = service.get_repository("my-repo")

        assert repo.name == "my-repo"

    def should_raise_when_getting_nonexistent_repository(self, service):
        with pytest.raises(ValueError, match="not found"):
            service.get_repository("nonexistent")

    def should_add_repository_with_custom_file_types(self, service):
        repo = service.add_repository("my-repo", "/tmp/docs", file_types=["md", "txt"])

        assert repo.file_types == ["md", "txt"]

    def should_add_repository_with_embedding_settings(self, service):
        repo = service.add_repository(
            "my-repo", "/tmp/docs", embedding_provider="ollama", embedding_model="nomic-embed-text"
        )

        assert repo.embedding_provider == "ollama"
        assert repo.embedding_model == "nomic-embed-text"


class DescribeRepositoryServiceUpdateRepository:
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    @pytest.fixture
    def config_gateway(self, temp_dir):
        return ConfigGateway(config_dir=temp_dir)

    @pytest.fixture
    def service(self, config_gateway):
        return RepositoryService(config_gateway=config_gateway)

    @pytest.fixture
    def existing_repo(self, service):
        return service.add_repository(
            "my-repo",
            "/tmp/docs",
            file_types=["md", "txt"],
            embedding_provider="chromadb",
            exclude_patterns=["node_modules"],
        )

    def should_add_new_patterns_to_existing(self, service, existing_repo):
        updated, _ = service.update_repository("my-repo", add_exclude_patterns=["dist"])

        assert "node_modules" in updated.exclude_patterns
        assert "dist" in updated.exclude_patterns

    def should_deduplicate_patterns(self, service, existing_repo):
        updated, added = service.update_repository("my-repo", add_exclude_patterns=["node_modules"])

        assert updated.exclude_patterns.count("node_modules") == 1
        assert added == []

    def should_preserve_order_of_patterns(self, service, existing_repo):
        updated, _ = service.update_repository("my-repo", add_exclude_patterns=["dist", "build"])

        assert updated.exclude_patterns == ["node_modules", "dist", "build"]

    def should_update_file_types_when_provided(self, service, existing_repo):
        updated, _ = service.update_repository("my-repo", file_types=["pdf"])

        assert updated.file_types == ["pdf"]

    def should_not_change_file_types_when_not_provided(self, service, existing_repo):
        updated, _ = service.update_repository("my-repo")

        assert updated.file_types == ["md", "txt"]

    def should_update_embedding_provider_when_provided(self, service, existing_repo):
        updated, _ = service.update_repository("my-repo", embedding_provider="ollama")

        assert updated.embedding_provider == "ollama"

    def should_not_change_embedding_provider_when_not_provided(self, service, existing_repo):
        updated, _ = service.update_repository("my-repo")

        assert updated.embedding_provider == "chromadb"

    def should_update_embedding_model_when_provided(self, service, existing_repo):
        updated, _ = service.update_repository("my-repo", embedding_model="nomic-embed-text")

        assert updated.embedding_model == "nomic-embed-text"

    def should_raise_when_repo_not_found(self, service):
        with pytest.raises(ValueError, match="not found"):
            service.update_repository("nonexistent")

    def should_return_added_patterns(self, service, existing_repo):
        _, added = service.update_repository("my-repo", add_exclude_patterns=["dist", "node_modules"])

        assert added == ["dist"]

    def should_persist_updates(self, service, config_gateway, existing_repo):
        service.update_repository("my-repo", file_types=["pdf"], add_exclude_patterns=["dist"])

        reloaded = service.get_repository("my-repo")
        assert reloaded.file_types == ["pdf"]
        assert "dist" in reloaded.exclude_patterns
