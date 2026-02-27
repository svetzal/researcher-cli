import json
import tempfile
from pathlib import Path

from researcher.cli.init_commands import run_init


class DescribeRunInit:
    def should_install_skills_to_target_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            result = run_init(target, json_output=True)

            assert "researcher-admin" in result["skills_installed"]
            assert "researcher-find" in result["skills_installed"]
            assert (target / ".claude" / "skills" / "researcher-admin" / "SKILL.md").exists()
            assert (target / ".claude" / "skills" / "researcher-find" / "SKILL.md").exists()

    def should_skip_existing_skills_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            run_init(target, json_output=True)

            result = run_init(target, json_output=True)

            assert result["skills_installed"] == []
            assert "researcher-admin" in result["skills_skipped"]
            assert "researcher-find" in result["skills_skipped"]

    def should_overwrite_existing_skills_with_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            run_init(target, json_output=True)

            skill_path = target / ".claude" / "skills" / "researcher-admin" / "SKILL.md"
            skill_path.write_text("old content")

            result = run_init(target, force=True, json_output=True)

            assert "researcher-admin" in result["skills_installed"]
            assert skill_path.read_text() != "old content"

    def should_create_claude_skills_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            run_init(target, json_output=True)

            assert (target / ".claude" / "skills" / "researcher-admin").is_dir()
            assert (target / ".claude" / "skills" / "researcher-find").is_dir()

    def should_output_json_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            result = run_init(target, json_output=True)

            serialized = json.dumps(result)
            parsed = json.loads(serialized)

            assert "skills_installed" in parsed
            assert "skills_skipped" in parsed
            assert "target_dir" in parsed
            assert parsed["target_dir"] == str(target)
