import sys
import tempfile
from pathlib import Path

import pytest

from researcher.config import RepositoryConfig, ResearcherConfig
from researcher.gateways.config_gateway import ConfigGateway
from researcher.service_factory import ServiceFactory
from researcher.services.index_service import IndexService
from researcher.services.repository_service import RepositoryService
from researcher.services.search_service import SearchService


class DescribeServiceFactory:
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as d:
            yield Path(d)

    @pytest.fixture
    def factory(self, temp_dir):
        return ServiceFactory(config_dir=temp_dir)

    def should_provide_config_gateway(self, factory):
        gateway = factory.config_gateway

        assert isinstance(gateway, ConfigGateway)

    def should_cache_config_gateway(self, factory):
        gateway1 = factory.config_gateway
        gateway2 = factory.config_gateway

        assert gateway1 is gateway2

    def should_provide_default_config_when_no_file(self, factory):
        config = factory.config

        assert isinstance(config, ResearcherConfig)
        assert config.repositories == []

    def should_cache_config(self, factory):
        config1 = factory.config
        config2 = factory.config

        assert config1 is config2

    def should_provide_repository_service(self, factory):
        service = factory.repository_service

        assert isinstance(service, RepositoryService)

    def should_cache_repository_service(self, factory):
        service1 = factory.repository_service
        service2 = factory.repository_service

        assert service1 is service2

    def should_create_index_service_for_repository(self, factory, temp_dir):
        repo = RepositoryConfig(name="test-repo", path=str(temp_dir))

        service = factory.index_service(repo)

        assert isinstance(service, IndexService)

    def should_create_new_index_service_each_call(self, factory, temp_dir):
        repo = RepositoryConfig(name="test-repo", path=str(temp_dir))

        service1 = factory.index_service(repo)
        service2 = factory.index_service(repo)

        assert service1 is not service2

    def should_create_search_service_for_repository(self, factory, temp_dir):
        repo = RepositoryConfig(name="test-repo", path=str(temp_dir))

        service = factory.search_service(repo)

        assert isinstance(service, SearchService)

    def should_create_new_search_service_each_call(self, factory, temp_dir):
        repo = RepositoryConfig(name="test-repo", path=str(temp_dir))

        service1 = factory.search_service(repo)
        service2 = factory.search_service(repo)

        assert service1 is not service2

    def should_create_index_service_with_vlm_pipeline(self, temp_dir):
        factory = ServiceFactory(config_dir=temp_dir, docling_available=True)
        repo = RepositoryConfig(name="my-repo", path=str(temp_dir), image_pipeline="vlm", image_vlm_model="smoldocling")

        service = factory.index_service(repo)

        assert isinstance(service, IndexService)

    def should_create_index_service_with_default_pipeline(self, temp_dir):
        factory = ServiceFactory(config_dir=temp_dir, docling_available=True)
        repo = RepositoryConfig(name="my-repo", path=str(temp_dir))

        service = factory.index_service(repo)

        assert isinstance(service, IndexService)

    def should_create_index_service_without_docling_when_unavailable(self, temp_dir):
        factory = ServiceFactory(config_dir=temp_dir, docling_available=False)
        repo = RepositoryConfig(name="my-repo", path=str(temp_dir))

        service = factory.index_service(repo)

        assert isinstance(service, IndexService)

    def should_probe_real_import_when_docling_available_not_overridden(self, temp_dir, monkeypatch):
        monkeypatch.setitem(sys.modules, "docling.document_converter", None)
        factory = ServiceFactory(config_dir=temp_dir)

        assert factory._docling_available is False

    def should_detect_docling_present_via_probe_when_not_overridden(self, temp_dir, monkeypatch):
        import types

        fake_module = types.ModuleType("docling.document_converter")
        monkeypatch.setitem(sys.modules, "docling.document_converter", fake_module)
        factory = ServiceFactory(config_dir=temp_dir)

        assert factory._docling_available is True
