"""Unit tests verifying that gateways translate third-party exceptions into domain exceptions."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from researcher.exceptions import (
    ConfigurationError,
    DocumentConversionError,
    EmbeddingError,
    ModelArchiveError,
    RepositoryAlreadyExistsError,
    RepositoryNotFoundError,
    ResearcherError,
    StorageError,
)

# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------


def should_storage_error_be_researcher_error():
    assert issubclass(StorageError, ResearcherError)


def should_embedding_error_be_researcher_error():
    assert issubclass(EmbeddingError, ResearcherError)


def should_document_conversion_error_be_researcher_error():
    assert issubclass(DocumentConversionError, ResearcherError)


def should_configuration_error_be_researcher_error():
    assert issubclass(ConfigurationError, ResearcherError)


def should_repository_not_found_error_be_researcher_error():
    assert issubclass(RepositoryNotFoundError, ResearcherError)


def should_repository_already_exists_error_be_researcher_error():
    assert issubclass(RepositoryAlreadyExistsError, ResearcherError)


def should_model_archive_error_be_researcher_error():
    assert issubclass(ModelArchiveError, ResearcherError)


# ---------------------------------------------------------------------------
# ChromaGateway → StorageError
# ---------------------------------------------------------------------------


def should_chroma_gateway_query_raise_storage_error(tmp_path):
    from researcher.gateways.chroma_gateway import ChromaGateway

    gw = ChromaGateway(tmp_path)
    with (
        patch.object(gw._client, "get_or_create_collection", side_effect=RuntimeError("boom")),
        pytest.raises(StorageError) as exc_info,
    ):
        gw.query("col", "hello")
    assert exc_info.value.__cause__ is not None


def should_chroma_gateway_init_raise_storage_error():
    from researcher.gateways.chroma_gateway import ChromaGateway

    with (
        patch("chromadb.PersistentClient", side_effect=RuntimeError("no disk")),
        pytest.raises(StorageError) as exc_info,
    ):
        ChromaGateway(Path("/nonexistent/path"))
    assert exc_info.value.__cause__ is not None


# ---------------------------------------------------------------------------
# OllamaEmbeddingGateway → EmbeddingError
# ---------------------------------------------------------------------------


def should_ollama_embedding_gateway_raise_embedding_error():
    from researcher.gateways.ollama_embedding_gateway import OllamaEmbeddingGateway

    gw = OllamaEmbeddingGateway(model="nomodel")
    fake_ollama = MagicMock()
    fake_ollama.embeddings.side_effect = ConnectionError("server not running")
    with (
        patch.dict("sys.modules", {"ollama": fake_ollama}),
        pytest.raises(EmbeddingError) as exc_info,
    ):
        gw.embed_texts(["test"])
    assert exc_info.value.__cause__ is not None


# ---------------------------------------------------------------------------
# OpenAIEmbeddingGateway → EmbeddingError
# ---------------------------------------------------------------------------


def should_openai_embedding_gateway_raise_embedding_error():
    from researcher.gateways.openai_embedding_gateway import OpenAIEmbeddingGateway

    gw = OpenAIEmbeddingGateway(model="text-embedding-ada-002")
    fake_openai = MagicMock()
    fake_openai.OpenAI.return_value.embeddings.create.side_effect = Exception("auth error")
    with (
        patch.dict("sys.modules", {"openai": fake_openai}),
        pytest.raises(EmbeddingError) as exc_info,
    ):
        gw.embed_texts(["test"])
    assert exc_info.value.__cause__ is not None


# ---------------------------------------------------------------------------
# DoclingGateway → DocumentConversionError
# ---------------------------------------------------------------------------


def should_docling_gateway_convert_raise_document_conversion_error(tmp_path):
    from researcher.gateways.docling_gateway import DoclingGateway

    gw = DoclingGateway()
    mock_converter = MagicMock()
    mock_converter.convert.side_effect = RuntimeError("corrupt file")
    gw._converter = mock_converter

    nonexistent = tmp_path / "bad.pdf"
    with pytest.raises(DocumentConversionError) as exc_info:
        gw.convert(nonexistent)
    assert exc_info.value.__cause__ is not None


def should_docling_gateway_missing_import_raise_document_conversion_error():
    from researcher.gateways.docling_gateway import DoclingGateway

    gw = DoclingGateway()
    with (
        patch("researcher.gateways.docling_gateway.build_document_converter", side_effect=ImportError("no docling")),
        pytest.raises(DocumentConversionError) as exc_info,
    ):
        gw._get_converter()
    assert "docling is not installed" in str(exc_info.value)
    assert exc_info.value.__cause__ is not None


# ---------------------------------------------------------------------------
# ConfigGateway → ConfigurationError
# ---------------------------------------------------------------------------


def should_config_gateway_load_bad_yaml_raise_configuration_error(tmp_path):
    from researcher.gateways.config_gateway import ConfigGateway

    bad_yaml = tmp_path / "config.yaml"
    bad_yaml.write_text("{{{invalid yaml")
    gw = ConfigGateway(config_dir=tmp_path)
    with pytest.raises(ConfigurationError) as exc_info:
        gw.load()
    assert exc_info.value.__cause__ is not None


# ---------------------------------------------------------------------------
# ChecksumGateway → StorageError
# ---------------------------------------------------------------------------


def should_checksum_gateway_load_bad_json_raise_storage_error(tmp_path):
    from researcher.gateways.checksum_gateway import ChecksumGateway

    bad_json = tmp_path / "checksums.json"
    bad_json.write_text("not valid json {{{")
    gw = ChecksumGateway(bad_json)
    with pytest.raises(StorageError) as exc_info:
        gw.load()
    assert exc_info.value.__cause__ is not None


# ---------------------------------------------------------------------------
# IndexService — unexpected exceptions propagate (not swallowed)
# ---------------------------------------------------------------------------


def should_index_service_propagate_unexpected_exception(tmp_path):
    from researcher.gateways.checksum_gateway import ChecksumGateway
    from researcher.gateways.chroma_gateway import ChromaGateway
    from researcher.gateways.filesystem_gateway import FilesystemGateway
    from researcher.services.index_service import IndexService

    config_mock = MagicMock()
    config_mock.file_types = ["txt"]
    config_mock.exclude_patterns = []
    config_mock.embedding_provider = "chromadb"
    config_mock.path = str(tmp_path)

    fs_gw = MagicMock(spec=FilesystemGateway)
    fs_gw.list_files.return_value = [tmp_path / "a.txt"]
    fs_gw.compute_checksum.side_effect = RuntimeError("unexpected!")

    chroma_gw = MagicMock(spec=ChromaGateway)
    chroma_gw.count.return_value = 0

    checksum_path = tmp_path / "checksums.json"
    checksum_gw = ChecksumGateway(checksum_path)

    service = IndexService(
        filesystem_gateway=fs_gw,
        docling_gateway=None,
        embedding_gateway=MagicMock(),
        chroma_gateway=chroma_gw,
        repo_name="test",
        checksum_gateway=checksum_gw,
    )

    with pytest.raises(RuntimeError, match="unexpected!"):
        service.index_repository(config_mock)
