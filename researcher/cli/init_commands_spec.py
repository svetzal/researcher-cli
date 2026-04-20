import json
import tempfile
from pathlib import Path

from researcher.cli.init_commands import _parse_frontmatter_version, run_init


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


class DescribeParseFrontmatterVersion:
    def should_extract_researcher_version(self):
        text = "---\nname: test\nresearcher-version: 1.2.3\n---\ncontent"
        assert _parse_frontmatter_version(text) == "1.2.3"

    def should_fallback_to_metadata_version(self):
        text = '---\nname: test\nmetadata:\n  version: "1.2.3"\n  author: Test\n---\ncontent'
        assert _parse_frontmatter_version(text) == "1.2.3"

    def should_prefer_researcher_version_over_metadata(self):
        text = '---\nname: test\nmetadata:\n  version: "1.0.0"\nresearcher-version: 2.0.0\n---\ncontent'
        assert _parse_frontmatter_version(text) == "2.0.0"

    def should_return_none_without_frontmatter(self):
        assert _parse_frontmatter_version("no frontmatter here") is None

    def should_return_none_for_empty_frontmatter(self):
        assert _parse_frontmatter_version("---\nname: test\n---\ncontent") is None
