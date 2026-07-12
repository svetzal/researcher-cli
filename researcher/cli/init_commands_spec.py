import json
from pathlib import Path
from unittest.mock import Mock, patch

from typer.testing import CliRunner

from researcher.cli.main import app
from researcher.exceptions import StorageError
from researcher.service_factory import ServiceFactory
from researcher.services.skill_install_service import SkillInstallService

runner = CliRunner()


class DescribeInitCommand:
    def should_exit_1_and_print_error_on_storage_error(self):
        mock_service = Mock(spec=SkillInstallService)
        mock_service.install.side_effect = StorageError("no space left")

        with patch.object(ServiceFactory, "skill_install_service", return_value=mock_service):
            result = runner.invoke(app, ["init"])

        assert result.exit_code == 1
        assert "no space left" in result.output

    def should_output_json_error_on_storage_error_with_json_flag(self):
        mock_service = Mock(spec=SkillInstallService)
        mock_service.install.side_effect = StorageError("no space left")

        with patch.object(ServiceFactory, "skill_install_service", return_value=mock_service):
            result = runner.invoke(app, ["init", "--json"])

        assert result.exit_code == 1
        parsed = json.loads(result.output)
        assert "error" in parsed
        assert "no space left" in parsed["error"]

    def should_emit_json_payload_with_expected_keys_on_success(self):
        mock_service = Mock(spec=SkillInstallService)
        mock_service.install.return_value = {
            "skills_installed": ["researcher-admin", "researcher-find"],
            "skills_skipped": [],
            "skills_refused": [],
            "version": "0.4.0",
            "target_dir": str(Path.cwd()),
        }

        with patch.object(ServiceFactory, "skill_install_service", return_value=mock_service):
            result = runner.invoke(app, ["init", "--json"])

        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert "skills_installed" in parsed
        assert "skills_skipped" in parsed
        assert "skills_refused" in parsed
        assert "version" in parsed
        assert "target_dir" in parsed
