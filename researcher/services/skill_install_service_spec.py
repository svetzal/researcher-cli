import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from researcher.exceptions import StorageError
from researcher.gateways.bundled_skills_gateway import BundledSkillsGateway
from researcher.gateways.filesystem_gateway import FilesystemGateway
from researcher.services.skill_install_service import (
    SkillInstallPlan,
    SkillInstallService,
    plan_skill_installs,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FRONTMATTER = '---\nname: {name}\nmetadata:\n  version: "0.3.0"\n---\ncontent\n'

ADMIN_SOURCE = _FRONTMATTER.format(name="researcher-admin")
FIND_SOURCE = _FRONTMATTER.format(name="researcher-find")

SOURCES = {
    "researcher-admin": ADMIN_SOURCE,
    "researcher-find": FIND_SOURCE,
}


def _stamped_existing(version: str) -> str:
    """Return a skill text that looks like it was stamped at *version*."""
    return (
        f'---\nname: researcher-admin\nresearcher-version: {version}\nmetadata:\n  version: "{version}"\n---\ncontent\n'
    )


# ---------------------------------------------------------------------------
# DescribePlanSkillInstalls — pure function, zero I/O
# ---------------------------------------------------------------------------


class DescribePlanSkillInstalls:
    def should_install_all_when_none_exist(self):
        existing = {"researcher-admin": None, "researcher-find": None}

        plan = plan_skill_installs(SOURCES, existing, "0.4.0", force=False)

        assert [name for name, _ in plan.to_write] == ["researcher-admin", "researcher-find"]
        assert plan.skipped == []
        assert plan.refused == []

    def should_stamp_version_in_written_text(self):
        existing = {"researcher-admin": None}

        plan = plan_skill_installs({"researcher-admin": ADMIN_SOURCE}, existing, "0.4.0", force=False)

        _, stamped = plan.to_write[0]
        assert "researcher-version: 0.4.0" in stamped

    def should_skip_when_same_version_installed(self):
        existing = {"researcher-admin": _stamped_existing("0.4.0")}

        plan = plan_skill_installs({"researcher-admin": ADMIN_SOURCE}, existing, "0.4.0", force=False)

        assert plan.to_write == []
        assert plan.skipped == ["researcher-admin"]
        assert plan.refused == []

    def should_refuse_when_installed_version_is_newer(self):
        existing = {"researcher-admin": _stamped_existing("0.5.0")}

        plan = plan_skill_installs({"researcher-admin": ADMIN_SOURCE}, existing, "0.4.0", force=False)

        assert plan.to_write == []
        assert plan.skipped == []
        assert plan.refused == ["researcher-admin"]

    def should_install_when_upgrading_older_version(self):
        existing = {"researcher-admin": _stamped_existing("0.3.0")}

        plan = plan_skill_installs({"researcher-admin": ADMIN_SOURCE}, existing, "0.4.0", force=False)

        assert [name for name, _ in plan.to_write] == ["researcher-admin"]
        assert plan.skipped == []
        assert plan.refused == []

    def should_force_bypass_refuse_for_downgrade(self):
        existing = {"researcher-admin": _stamped_existing("0.5.0")}

        plan = plan_skill_installs({"researcher-admin": ADMIN_SOURCE}, existing, "0.4.0", force=True)

        assert [name for name, _ in plan.to_write] == ["researcher-admin"]
        assert plan.refused == []

    def should_skip_even_with_force_when_same_version(self):
        existing = {"researcher-admin": _stamped_existing("0.4.0")}

        plan = plan_skill_installs({"researcher-admin": ADMIN_SOURCE}, existing, "0.4.0", force=True)

        assert plan.to_write == []
        assert plan.skipped == ["researcher-admin"]

    def should_install_when_existing_has_no_version_field(self):
        existing = {"researcher-admin": "---\nname: researcher-admin\n---\nold content"}

        plan = plan_skill_installs({"researcher-admin": ADMIN_SOURCE}, existing, "0.4.0", force=False)

        assert [name for name, _ in plan.to_write] == ["researcher-admin"]

    def should_return_frozen_plan(self):
        plan = plan_skill_installs(SOURCES, {"researcher-admin": None, "researcher-find": None}, "0.4.0", force=False)

        assert isinstance(plan, SkillInstallPlan)

    def should_output_json_serialisable_result(self):
        existing = {"researcher-admin": None, "researcher-find": None}

        plan = plan_skill_installs(SOURCES, existing, "0.4.0", force=False)

        payload = {"to_write": [[n, t] for n, t in plan.to_write], "skipped": plan.skipped, "refused": plan.refused}
        serialized = json.dumps(payload)
        parsed = json.loads(serialized)
        assert "to_write" in parsed


# ---------------------------------------------------------------------------
# DescribeSkillInstallService — imperative shell with mocked gateways
# ---------------------------------------------------------------------------


class DescribeSkillInstallService:
    @pytest.fixture
    def mock_fs(self):
        mock = Mock(spec=FilesystemGateway)
        mock.file_exists.return_value = False
        mock.read_file.return_value = None
        mock.make_directories.return_value = None
        mock.write_file.return_value = None
        return mock

    @pytest.fixture
    def mock_bundled(self):
        mock = Mock(spec=BundledSkillsGateway)
        mock.package_version.return_value = "0.4.0"
        mock.read_skill_source.side_effect = lambda name: _FRONTMATTER.format(name=name)
        return mock

    @pytest.fixture
    def service(self, mock_fs, mock_bundled):
        return SkillInstallService(
            filesystem_gateway=mock_fs,
            bundled_skills_gateway=mock_bundled,
            skill_names=["researcher-admin", "researcher-find"],
        )

    def should_install_both_skills_when_none_exist(self, service, mock_fs):
        result = service.install(Path("/tmp/target"))

        assert "researcher-admin" in result["skills_installed"]
        assert "researcher-find" in result["skills_installed"]
        assert result["skills_skipped"] == []
        assert result["skills_refused"] == []

    def should_write_files_via_filesystem_gateway(self, service, mock_fs):
        service.install(Path("/tmp/target"))

        assert mock_fs.write_file.call_count == 2

    def should_create_directories_before_writing(self, service, mock_fs):
        service.install(Path("/tmp/target"))

        assert mock_fs.make_directories.call_count == 2

    def should_return_correct_version_in_result(self, service):
        result = service.install(Path("/tmp/target"))

        assert result["version"] == "0.4.0"

    def should_return_target_dir_in_result(self, service):
        result = service.install(Path("/tmp/target"))

        assert result["target_dir"] == "/tmp/target"

    def should_read_version_from_bundled_skills_gateway(self, service, mock_bundled):
        service.install(Path("/tmp/target"))

        mock_bundled.package_version.assert_called_once()

    def should_skip_when_same_version_already_installed(self, mock_fs, mock_bundled):
        mock_fs.file_exists.return_value = True
        mock_fs.read_file.return_value = _stamped_existing("0.4.0")
        service = SkillInstallService(
            filesystem_gateway=mock_fs,
            bundled_skills_gateway=mock_bundled,
            skill_names=["researcher-admin"],
        )

        result = service.install(Path("/tmp/target"))

        assert result["skills_installed"] == []
        assert "researcher-admin" in result["skills_skipped"]
        mock_fs.write_file.assert_not_called()

    def should_refuse_when_installed_version_is_newer(self, mock_fs, mock_bundled):
        mock_fs.file_exists.return_value = True
        mock_fs.read_file.return_value = _stamped_existing("0.5.0")
        service = SkillInstallService(
            filesystem_gateway=mock_fs,
            bundled_skills_gateway=mock_bundled,
            skill_names=["researcher-admin"],
        )

        result = service.install(Path("/tmp/target"))

        assert result["skills_installed"] == []
        assert "researcher-admin" in result["skills_refused"]
        mock_fs.write_file.assert_not_called()

    def should_force_install_when_newer_version_installed(self, mock_fs, mock_bundled):
        mock_fs.file_exists.return_value = True
        mock_fs.read_file.return_value = _stamped_existing("0.5.0")
        service = SkillInstallService(
            filesystem_gateway=mock_fs,
            bundled_skills_gateway=mock_bundled,
            skill_names=["researcher-admin"],
        )

        result = service.install(Path("/tmp/target"), force=True)

        assert "researcher-admin" in result["skills_installed"]

    def should_propagate_storage_error_from_gateway(self, mock_fs, mock_bundled):
        mock_fs.file_exists.return_value = False
        mock_fs.write_file.side_effect = StorageError("disk full")
        service = SkillInstallService(
            filesystem_gateway=mock_fs,
            bundled_skills_gateway=mock_bundled,
            skill_names=["researcher-admin"],
        )

        with pytest.raises(StorageError, match="disk full"):
            service.install(Path("/tmp/target"))
