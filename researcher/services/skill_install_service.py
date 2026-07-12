"""Service for installing bundled Claude Code skills."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from researcher.gateways.bundled_skills_gateway import BundledSkillsGateway
from researcher.gateways.filesystem_gateway import FilesystemGateway
from researcher.services.skill_versioning import decide_skill_action, stamp_version

SKILLS = ["researcher-admin", "researcher-find"]


class SkillInstallPlan(BaseModel):
    """Pure data describing what the installer should do — no I/O."""

    model_config = ConfigDict(frozen=True)

    to_write: list[tuple[str, str]]  # (skill_name, stamped_text)
    skipped: list[str]
    refused: list[str]


def plan_skill_installs(
    sources: dict[str, str],
    existing: dict[str, str | None],
    version: str,
    *,
    force: bool,
) -> SkillInstallPlan:
    """Pure planning function — decides what to install, skip, or refuse.

    Args:
        sources: Mapping of skill_name → raw source text.
        existing: Mapping of skill_name → installed text (None if absent).
        version: The package version to stamp into installed skills.
        force: When True, bypass the version guard on downgrades.

    Returns:
        A frozen ``SkillInstallPlan`` describing the actions to take.
    """
    to_write: list[tuple[str, str]] = []
    skipped: list[str] = []
    refused: list[str] = []

    for skill_name, source_text in sources.items():
        existing_text = existing.get(skill_name)
        action, _message = decide_skill_action(existing_text, version, force=force)

        if action == "refuse":
            refused.append(skill_name)
        elif action == "skip":
            skipped.append(skill_name)
        else:
            stamped = stamp_version(source_text, version)
            to_write.append((skill_name, stamped))

    return SkillInstallPlan(to_write=to_write, skipped=skipped, refused=refused)


class SkillInstallService:
    """Imperative shell that reads sources, plans, and writes skill files."""

    def __init__(
        self,
        filesystem_gateway: FilesystemGateway,
        bundled_skills_gateway: BundledSkillsGateway,
        skill_names: list[str] | None = None,
    ) -> None:
        self._fs = filesystem_gateway
        self._bundled = bundled_skills_gateway
        self._skill_names = skill_names if skill_names is not None else SKILLS

    def install(self, target_dir: Path, *, force: bool = False) -> dict:
        """Install bundled skills into target_dir/.claude/skills/.

        Args:
            target_dir: Root directory under which ``.claude/skills/`` lives.
            force: When True, bypass the version guard on downgrades.

        Returns:
            Dict with keys ``skills_installed``, ``skills_skipped``,
            ``skills_refused``, ``version``, and ``target_dir``.
        """
        skills_dir = target_dir / ".claude" / "skills"
        version = self._bundled.package_version()

        sources = {name: self._bundled.read_skill_source(name) for name in self._skill_names}

        existing: dict[str, str | None] = {}
        for name in self._skill_names:
            dest = skills_dir / name / "SKILL.md"
            existing[name] = self._fs.read_file(dest) if self._fs.file_exists(dest) else None

        plan = plan_skill_installs(sources, existing, version, force=force)

        installed: list[str] = []
        for skill_name, stamped_text in plan.to_write:
            dest = skills_dir / skill_name / "SKILL.md"
            self._fs.make_directories(dest.parent)
            self._fs.write_file(dest, stamped_text)
            installed.append(skill_name)

        return {
            "skills_installed": installed,
            "skills_skipped": plan.skipped,
            "skills_refused": plan.refused,
            "version": version,
            "target_dir": str(target_dir),
        }
