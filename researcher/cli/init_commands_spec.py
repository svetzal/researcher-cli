import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from researcher.cli.init_commands import run_init
from researcher.cli.main import app
from researcher.exceptions import StorageError
from researcher.gateways.filesystem_gateway import FilesystemGateway


class DescribeRunInit:
    def should_install_skills_to_target_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            result = run_init(target, _version="0.4.0")

            assert "researcher-admin" in result["skills_installed"]
            assert "researcher-find" in result["skills_installed"]
            assert (target / ".claude" / "skills" / "researcher-admin" / "SKILL.md").exists()
            assert (target / ".claude" / "skills" / "researcher-find" / "SKILL.md").exists()

    def should_stamp_version_in_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            run_init(target, _version="0.4.0")

            content = (target / ".claude" / "skills" / "researcher-admin" / "SKILL.md").read_text()
            assert "researcher-version: 0.4.0" in content

    def should_stamp_metadata_version_in_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            run_init(target, _version="0.4.0")

            content = (target / ".claude" / "skills" / "researcher-admin" / "SKILL.md").read_text()
            assert 'version: "0.4.0"' in content

    def should_overwrite_older_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            run_init(target, _version="0.3.0")

            result = run_init(target, _version="0.4.0")

            assert "researcher-admin" in result["skills_installed"]
            assert "researcher-find" in result["skills_installed"]
            content = (target / ".claude" / "skills" / "researcher-admin" / "SKILL.md").read_text()
            assert "researcher-version: 0.4.0" in content

    def should_skip_same_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            run_init(target, _version="0.4.0")

            result = run_init(target, _version="0.4.0")

            assert result["skills_installed"] == []
            assert "researcher-admin" in result["skills_skipped"]
            assert "researcher-find" in result["skills_skipped"]

    def should_refuse_newer_version_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            run_init(target, _version="0.5.0")

            result = run_init(target, _version="0.4.0")

            assert result["skills_installed"] == []
            assert "researcher-admin" in result["skills_refused"]
            assert "researcher-find" in result["skills_refused"]

    def should_force_bypass_version_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            run_init(target, _version="0.5.0")

            result = run_init(target, force=True, _version="0.4.0")

            assert "researcher-admin" in result["skills_installed"]
            assert "researcher-find" in result["skills_installed"]
            content = (target / ".claude" / "skills" / "researcher-admin" / "SKILL.md").read_text()
            assert "researcher-version: 0.4.0" in content

    def should_skip_existing_skills_without_force(self):
        """Files with no version field are always overwritten (treated as legacy)."""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            run_init(target, _version="0.4.0")

            # Simulate a legacy file with no version field
            skill_path = target / ".claude" / "skills" / "researcher-admin" / "SKILL.md"
            skill_path.write_text("---\nname: researcher-admin\n---\nold content")

            result = run_init(target, _version="0.4.0")

            assert "researcher-admin" in result["skills_installed"]

    def should_overwrite_legacy_files_without_version_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            run_init(target, _version="0.4.0")

            skill_path = target / ".claude" / "skills" / "researcher-admin" / "SKILL.md"
            skill_path.write_text("old content")

            result = run_init(target, _version="0.4.0")

            assert "researcher-admin" in result["skills_installed"]
            assert skill_path.read_text() != "old content"

    def should_skip_same_version_even_with_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            run_init(target, _version="0.4.0")

            result = run_init(target, force=True, _version="0.4.0")

            assert result["skills_installed"] == []
            assert "researcher-admin" in result["skills_skipped"]
            assert "researcher-find" in result["skills_skipped"]

    def should_create_claude_skills_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            run_init(target, _version="0.4.0")

            assert (target / ".claude" / "skills" / "researcher-admin").is_dir()
            assert (target / ".claude" / "skills" / "researcher-find").is_dir()

    def should_install_skills_to_home_directory_for_global(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            result = run_init(target, _version="0.4.0")

            assert (target / ".claude" / "skills" / "researcher-admin" / "SKILL.md").exists()
            assert (target / ".claude" / "skills" / "researcher-find" / "SKILL.md").exists()
            assert result["target_dir"] == str(target)

    def should_output_json_results_with_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            result = run_init(target, _version="0.4.0")

            serialized = json.dumps(result)
            parsed = json.loads(serialized)

            assert "skills_installed" in parsed
            assert "skills_skipped" in parsed
            assert "skills_refused" in parsed
            assert "version" in parsed
            assert parsed["version"] == "0.4.0"
            assert parsed["target_dir"] == str(target)

    def should_propagate_storage_error_from_gateway(self):
        stub_gateway = Mock(spec=FilesystemGateway)
        stub_gateway.file_exists.return_value = False
        stub_gateway.make_directories.return_value = None
        stub_gateway.write_file.side_effect = StorageError("disk full")

        with tempfile.TemporaryDirectory() as tmp, pytest.raises(StorageError, match="disk full"):
            run_init(Path(tmp), _version="0.4.0", filesystem_gateway=stub_gateway)


runner = CliRunner()


class DescribeInitCommand:
    def should_exit_1_and_print_error_on_storage_error(self):
        with patch("researcher.cli.init_commands.run_init", side_effect=StorageError("no space left")):
            result = runner.invoke(app, ["init"])

        assert result.exit_code == 1
        assert "no space left" in result.output

    def should_output_json_error_on_storage_error_with_json_flag(self):
        with patch("researcher.cli.init_commands.run_init", side_effect=StorageError("no space left")):
            result = runner.invoke(app, ["init", "--json"])

        assert result.exit_code == 1
        parsed = json.loads(result.output)
        assert "error" in parsed
        assert "no space left" in parsed["error"]
