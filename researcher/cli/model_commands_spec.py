import json
from pathlib import Path
from unittest.mock import Mock

from typer.testing import CliRunner

from researcher.cli.model_commands import models_app
from researcher.conftest import make_repo
from researcher.exceptions import ModelArchiveError
from researcher.model_registry import ModelCacheEntry
from researcher.services.model_archive_service import ModelArchiveService, PackResult, UnpackResult

runner = CliRunner()


def _make_entry(category: str = "docling", archive_path: str = "docling/models") -> ModelCacheEntry:
    return ModelCacheEntry(
        category=category,
        source_path=Path("/tmp/cache") / category,
        archive_path=archive_path,
    )


def _make_pack_result(
    archive_path: str = "/tmp/models.tar.gz",
    total_files: int = 5,
    entries: list[ModelCacheEntry] | None = None,
) -> PackResult:
    if entries is None:
        entries = [_make_entry()]
    return PackResult(
        archive_path=Path(archive_path),
        entries=entries,
        total_files=total_files,
    )


def _make_unpack_result(entries_restored: int = 2, files_extracted: int = 10) -> UnpackResult:
    return UnpackResult(entries_restored=entries_restored, files_extracted=files_extracted)


class DescribeModelsCallback:
    def should_create_factory_when_ctx_obj_is_none(self):
        result = runner.invoke(models_app, ["--help"])

        assert result.exit_code == 0

    def should_use_existing_factory_when_ctx_obj_is_set(self, mock_factory):
        mock_factory.repository_service.list_repositories.return_value = []

        result = runner.invoke(models_app, ["pack", "--output", "/tmp/out.tar.gz"], obj=mock_factory)

        assert result.exit_code == 0
        assert "No repositories" in result.output


class DescribePackCommand:
    class DescribeRichOutput:
        def should_display_success_message_with_file_count(self, mock_factory):
            mock_factory.repository_service.list_repositories.return_value = [make_repo("my-notes")]
            mock_service = Mock(spec=ModelArchiveService)
            mock_service.pack.return_value = _make_pack_result(total_files=7)
            mock_factory.model_archive_service.return_value = mock_service

            result = runner.invoke(models_app, ["pack", "--output", "/tmp/models.tar.gz"], obj=mock_factory)

            assert result.exit_code == 0
            assert "7" in result.output

        def should_display_archive_path_in_output(self, mock_factory):
            mock_factory.repository_service.list_repositories.return_value = [make_repo("my-notes")]
            mock_service = Mock(spec=ModelArchiveService)
            mock_service.pack.return_value = _make_pack_result(archive_path="/tmp/models.tar.gz")
            mock_factory.model_archive_service.return_value = mock_service

            result = runner.invoke(models_app, ["pack", "--output", "/tmp/models.tar.gz"], obj=mock_factory)

            assert result.exit_code == 0
            assert "/tmp/models.tar.gz" in result.output

        def should_include_entries_in_table(self, mock_factory):
            entries = [
                _make_entry(category="docling", archive_path="docling/models"),
                _make_entry(category="huggingface", archive_path="huggingface/hub/models--org--repo"),
            ]
            mock_factory.repository_service.list_repositories.return_value = [make_repo("my-notes")]
            mock_service = Mock(spec=ModelArchiveService)
            mock_service.pack.return_value = _make_pack_result(entries=entries, total_files=3)
            mock_factory.model_archive_service.return_value = mock_service

            result = runner.invoke(models_app, ["pack", "--output", "/tmp/models.tar.gz"], obj=mock_factory)

            assert result.exit_code == 0
            assert "docling" in result.output
            assert "huggingface" in result.output

        def should_exit_zero_with_message_when_no_repos_configured(self, mock_factory):
            mock_factory.repository_service.list_repositories.return_value = []

            result = runner.invoke(models_app, ["pack", "--output", "/tmp/models.tar.gz"], obj=mock_factory)

            assert result.exit_code == 0
            assert "No repositories" in result.output

        def should_error_on_file_not_found(self, mock_factory):
            mock_factory.repository_service.list_repositories.return_value = [make_repo("my-notes")]
            mock_service = Mock(spec=ModelArchiveService)
            mock_service.pack.side_effect = ModelArchiveError("No model cache directories found on disk to pack.")
            mock_factory.model_archive_service.return_value = mock_service

            result = runner.invoke(models_app, ["pack", "--output", "/tmp/models.tar.gz"], obj=mock_factory)

            assert result.exit_code == 1
            assert "Error" in result.output

    class DescribeJsonOutput:
        def should_write_valid_json_on_success(self, mock_factory):
            entries = [_make_entry(category="docling", archive_path="docling/models")]
            mock_factory.repository_service.list_repositories.return_value = [make_repo("my-notes")]
            mock_service = Mock(spec=ModelArchiveService)
            mock_service.pack.return_value = _make_pack_result(
                archive_path="/tmp/models.tar.gz",
                total_files=4,
                entries=entries,
            )
            mock_factory.model_archive_service.return_value = mock_service

            result = runner.invoke(models_app, ["pack", "--output", "/tmp/models.tar.gz", "--json"], obj=mock_factory)

            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["archive"] == "/tmp/models.tar.gz"
            assert data["total_files"] == 4
            assert isinstance(data["entries"], list)
            assert len(data["entries"]) == 1
            assert data["entries"][0]["category"] == "docling"
            assert data["entries"][0]["archive_path"] == "docling/models"

        def should_accept_short_json_flag(self, mock_factory):
            mock_factory.repository_service.list_repositories.return_value = [make_repo("my-notes")]
            mock_service = Mock(spec=ModelArchiveService)
            mock_service.pack.return_value = _make_pack_result()
            mock_factory.model_archive_service.return_value = mock_service

            result = runner.invoke(models_app, ["pack", "--output", "/tmp/models.tar.gz", "-j"], obj=mock_factory)

            assert result.exit_code == 0
            data = json.loads(result.output)
            assert "archive" in data

        def should_write_empty_json_when_no_repos(self, mock_factory):
            mock_factory.repository_service.list_repositories.return_value = []

            result = runner.invoke(models_app, ["pack", "--output", "/tmp/models.tar.gz", "--json"], obj=mock_factory)

            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data == {"repositories": []}

        def should_write_error_json_on_file_not_found(self, mock_factory):
            mock_factory.repository_service.list_repositories.return_value = [make_repo("my-notes")]
            mock_service = Mock(spec=ModelArchiveService)
            mock_service.pack.side_effect = ModelArchiveError("No model cache directories found on disk to pack.")
            mock_factory.model_archive_service.return_value = mock_service

            result = runner.invoke(models_app, ["pack", "--output", "/tmp/models.tar.gz", "--json"], obj=mock_factory)

            assert result.exit_code == 1
            data = json.loads(result.output)
            assert "error" in data
            assert "No model cache" in data["error"]


class DescribeUnpackCommand:
    class DescribeRichOutput:
        def should_display_success_message_with_counts(self, mock_factory):
            mock_service = Mock(spec=ModelArchiveService)
            mock_service.unpack.return_value = _make_unpack_result(entries_restored=3, files_extracted=15)
            mock_factory.model_archive_service.return_value = mock_service

            result = runner.invoke(models_app, ["unpack", "/tmp/models.tar.gz"], obj=mock_factory)

            assert result.exit_code == 0
            assert "15" in result.output
            assert "3" in result.output

        def should_include_archive_path_in_output(self, mock_factory):
            mock_service = Mock(spec=ModelArchiveService)
            mock_service.unpack.return_value = _make_unpack_result()
            mock_factory.model_archive_service.return_value = mock_service

            result = runner.invoke(models_app, ["unpack", "/tmp/models.tar.gz"], obj=mock_factory)

            assert result.exit_code == 0
            assert "/tmp/models.tar.gz" in result.output

        def should_error_on_file_not_found(self, mock_factory):
            mock_service = Mock(spec=ModelArchiveService)
            mock_service.unpack.side_effect = ModelArchiveError("Archive not found: /tmp/missing.tar.gz")
            mock_factory.model_archive_service.return_value = mock_service

            result = runner.invoke(models_app, ["unpack", "/tmp/missing.tar.gz"], obj=mock_factory)

            assert result.exit_code == 1
            assert "Error" in result.output

        def should_error_on_value_error(self, mock_factory):
            mock_service = Mock(spec=ModelArchiveService)
            mock_service.unpack.side_effect = ModelArchiveError("Archive is missing manifest.json")
            mock_factory.model_archive_service.return_value = mock_service

            result = runner.invoke(models_app, ["unpack", "/tmp/bad.tar.gz"], obj=mock_factory)

            assert result.exit_code == 1
            assert "Error" in result.output

    class DescribeJsonOutput:
        def should_write_valid_json_on_success(self, mock_factory):
            mock_service = Mock(spec=ModelArchiveService)
            mock_service.unpack.return_value = _make_unpack_result(entries_restored=2, files_extracted=8)
            mock_factory.model_archive_service.return_value = mock_service

            result = runner.invoke(models_app, ["unpack", "/tmp/models.tar.gz", "--json"], obj=mock_factory)

            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["archive"] == "/tmp/models.tar.gz"
            assert data["entries_restored"] == 2
            assert data["files_extracted"] == 8

        def should_accept_short_json_flag(self, mock_factory):
            mock_service = Mock(spec=ModelArchiveService)
            mock_service.unpack.return_value = _make_unpack_result()
            mock_factory.model_archive_service.return_value = mock_service

            result = runner.invoke(models_app, ["unpack", "/tmp/models.tar.gz", "-j"], obj=mock_factory)

            assert result.exit_code == 0
            data = json.loads(result.output)
            assert "archive" in data

        def should_write_error_json_on_file_not_found(self, mock_factory):
            mock_service = Mock(spec=ModelArchiveService)
            mock_service.unpack.side_effect = ModelArchiveError("Archive not found: /tmp/missing.tar.gz")
            mock_factory.model_archive_service.return_value = mock_service

            result = runner.invoke(models_app, ["unpack", "/tmp/missing.tar.gz", "--json"], obj=mock_factory)

            assert result.exit_code == 1
            data = json.loads(result.output)
            assert "error" in data
            assert "Archive not found" in data["error"]

        def should_write_error_json_on_value_error(self, mock_factory):
            mock_service = Mock(spec=ModelArchiveService)
            mock_service.unpack.side_effect = ModelArchiveError("Archive is missing manifest.json")
            mock_factory.model_archive_service.return_value = mock_service

            result = runner.invoke(models_app, ["unpack", "/tmp/bad.tar.gz", "--json"], obj=mock_factory)

            assert result.exit_code == 1
            data = json.loads(result.output)
            assert "error" in data
            assert "manifest" in data["error"]
