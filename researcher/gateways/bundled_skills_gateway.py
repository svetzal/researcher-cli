from importlib.metadata import version as pkg_version
from importlib.resources import files

from researcher.gateways.error_wrapper import wrap_storage_error


class BundledSkillsGateway:
    """Gateway for accessing bundled skill files and package metadata."""

    @wrap_storage_error("Failed to read bundled skill '{skill_name}': {e}")
    def read_skill_source(self, skill_name: str) -> str:
        """Read the SKILL.md source text for the named bundled skill."""
        return files("researcher.bundled_skills").joinpath(skill_name, "SKILL.md").read_text()

    @wrap_storage_error("Failed to read package version: {e}")
    def package_version(self) -> str:
        """Return the installed researcher-cli package version string."""
        return pkg_version("researcher-cli")
