from researcher.config import RepositoryConfig, ResearcherConfig


class DescribeRepositoryConfig:
    def should_have_default_file_types(self):
        config = RepositoryConfig(name="test", path="/tmp/docs")

        assert "md" in config.file_types
        assert "pdf" in config.file_types
        assert config.embedding_provider == "chromadb"

    def should_accept_custom_file_types(self):
        config = RepositoryConfig(name="test", path="/tmp/docs", file_types=["md", "txt"])

        assert config.file_types == ["md", "txt"]

    def should_default_exclude_patterns_to_dot_folders(self):
        config = RepositoryConfig(name="test", path="/tmp/docs")

        assert config.exclude_patterns == [".*"]

    def should_accept_custom_exclude_patterns(self):
        config = RepositoryConfig(name="test", path="/tmp/docs", exclude_patterns=["node_modules", ".*"])

        assert config.exclude_patterns == ["node_modules", ".*"]

    def should_default_image_pipeline_to_standard(self):
        config = RepositoryConfig(name="test", path="/tmp/docs")

        assert config.image_pipeline == "standard"

    def should_default_image_vlm_model_to_none(self):
        config = RepositoryConfig(name="test", path="/tmp/docs")

        assert config.image_vlm_model is None

    def should_accept_vlm_image_pipeline(self):
        config = RepositoryConfig(name="test", path="/tmp/docs", image_pipeline="vlm", image_vlm_model="smoldocling")

        assert config.image_pipeline == "vlm"
        assert config.image_vlm_model == "smoldocling"

    def should_default_audio_asr_model_to_turbo(self):
        config = RepositoryConfig(name="test", path="/tmp/docs")

        assert config.audio_asr_model == "turbo"

    def should_accept_custom_audio_asr_model(self):
        config = RepositoryConfig(name="test", path="/tmp/docs", audio_asr_model="small")

        assert config.audio_asr_model == "small"


class DescribeResearcherConfig:
    def should_have_empty_repositories_by_default(self):
        config = ResearcherConfig()

        assert config.repositories == []
        assert config.default_embedding_provider == "chromadb"
        assert config.mcp_port == 8392
