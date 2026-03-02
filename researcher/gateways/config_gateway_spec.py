import tempfile
from pathlib import Path

import pytest

from researcher.config import RepositoryConfig, ResearcherConfig
from researcher.gateways.config_gateway import ConfigGateway


class DescribeConfigGateway:
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    @pytest.fixture
    def gateway(self, temp_dir):
        return ConfigGateway(config_dir=temp_dir)

    def should_return_default_config_when_file_absent(self, gateway):
        config = gateway.load()

        assert isinstance(config, ResearcherConfig)
        assert config.repositories == []

    def should_save_and_reload_config(self, gateway):
        config = ResearcherConfig(
            repositories=[RepositoryConfig(name="my-repo", path="/tmp/docs")],
            mcp_port=9000,
        )

        gateway.save(config)
        loaded = gateway.load()

        assert len(loaded.repositories) == 1
        assert loaded.repositories[0].name == "my-repo"
        assert loaded.mcp_port == 9000

    def should_create_directory_on_save(self, temp_dir):
        nested_dir = temp_dir / "a" / "b" / "c"
        gateway = ConfigGateway(config_dir=nested_dir)

        gateway.save(ResearcherConfig())

        assert nested_dir.exists()

    def should_preserve_repository_config_on_roundtrip(self, gateway):
        repo = RepositoryConfig(
            name="test",
            path="/tmp/test",
            file_types=["md", "pdf"],
            embedding_provider="ollama",
            embedding_model="nomic-embed-text",
        )
        config = ResearcherConfig(repositories=[repo])

        gateway.save(config)
        loaded = gateway.load()

        assert loaded.repositories[0].embedding_provider == "ollama"
        assert loaded.repositories[0].embedding_model == "nomic-embed-text"

    def should_serialise_and_deserialise_exclude_patterns(self, gateway):
        repo = RepositoryConfig(
            name="test",
            path="/tmp/test",
            exclude_patterns=["node_modules", ".*"],
        )
        config = ResearcherConfig(repositories=[repo])

        gateway.save(config)
        loaded = gateway.load()

        assert loaded.repositories[0].exclude_patterns == ["node_modules", ".*"]

    def should_deserialise_missing_exclude_patterns_as_default(self, gateway):
        raw_yaml = "repositories:\n- name: test\n  path: /tmp/test\n"
        config_file = gateway.config_dir / "config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(raw_yaml)

        loaded = gateway.load()

        assert loaded.repositories[0].exclude_patterns == [".*"]

    def should_serialise_and_deserialise_image_pipeline_settings(self, gateway):
        repo = RepositoryConfig(
            name="test",
            path="/tmp/test",
            image_pipeline="vlm",
            image_vlm_model="smoldocling",
        )
        config = ResearcherConfig(repositories=[repo])

        gateway.save(config)
        loaded = gateway.load()

        assert loaded.repositories[0].image_pipeline == "vlm"
        assert loaded.repositories[0].image_vlm_model == "smoldocling"

    def should_deserialise_missing_image_pipeline_as_standard(self, gateway):
        raw_yaml = "repositories:\n- name: test\n  path: /tmp/test\n"
        config_file = gateway.config_dir / "config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(raw_yaml)

        loaded = gateway.load()

        assert loaded.repositories[0].image_pipeline == "standard"
        assert loaded.repositories[0].image_vlm_model is None

    def should_serialise_and_deserialise_audio_asr_model(self, gateway):
        repo = RepositoryConfig(
            name="test",
            path="/tmp/test",
            audio_asr_model="small",
        )
        config = ResearcherConfig(repositories=[repo])

        gateway.save(config)
        loaded = gateway.load()

        assert loaded.repositories[0].audio_asr_model == "small"

    def should_deserialise_missing_audio_asr_model_as_turbo(self, gateway):
        raw_yaml = "repositories:\n- name: test\n  path: /tmp/test\n"
        config_file = gateway.config_dir / "config.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(raw_yaml)

        loaded = gateway.load()

        assert loaded.repositories[0].audio_asr_model == "turbo"
