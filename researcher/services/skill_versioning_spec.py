from researcher.services.skill_versioning import decide_skill_action, parse_frontmatter_version, stamp_version


class DescribeParseFrontmatterVersion:
    def should_extract_researcher_version(self):
        text = "---\nname: test\nresearcher-version: 1.2.3\n---\ncontent"
        assert parse_frontmatter_version(text) == "1.2.3"

    def should_fallback_to_metadata_version(self):
        text = '---\nname: test\nmetadata:\n  version: "1.2.3"\n  author: Test\n---\ncontent'
        assert parse_frontmatter_version(text) == "1.2.3"

    def should_prefer_researcher_version_over_metadata(self):
        text = '---\nname: test\nmetadata:\n  version: "1.0.0"\nresearcher-version: 2.0.0\n---\ncontent'
        assert parse_frontmatter_version(text) == "2.0.0"

    def should_return_none_without_frontmatter(self):
        assert parse_frontmatter_version("no frontmatter here") is None

    def should_return_none_for_empty_frontmatter(self):
        assert parse_frontmatter_version("---\nname: test\n---\ncontent") is None


class DescribeStampVersion:
    def should_insert_researcher_version(self):
        text = "---\nname: test\n---\ncontent"
        result = stamp_version(text, "1.2.3")
        assert "researcher-version: 1.2.3" in result

    def should_update_metadata_version(self):
        text = '---\nname: test\nmetadata:\n  version: "0.1.0"\n---\ncontent'
        result = stamp_version(text, "1.2.3")
        assert 'version: "1.2.3"' in result

    def should_passthrough_when_no_frontmatter(self):
        text = "no frontmatter here"
        assert stamp_version(text, "1.2.3") == text


class DescribeDecideSkillAction:
    def should_install_when_absent(self):
        action, _ = decide_skill_action(None, "1.0.0", force=False)
        assert action == "install"

    def should_install_when_no_version_field(self):
        text = "---\nname: test\n---\ncontent"
        action, _ = decide_skill_action(text, "1.0.0", force=False)
        assert action == "install"

    def should_install_on_upgrade(self):
        text = "---\nname: test\nresearcher-version: 0.9.0\n---\ncontent"
        action, _ = decide_skill_action(text, "1.0.0", force=False)
        assert action == "install"

    def should_skip_on_equal_version(self):
        text = "---\nname: test\nresearcher-version: 1.0.0\n---\ncontent"
        action, _ = decide_skill_action(text, "1.0.0", force=False)
        assert action == "skip"

    def should_refuse_on_newer_installed(self):
        text = "---\nname: test\nresearcher-version: 2.0.0\n---\ncontent"
        action, _ = decide_skill_action(text, "1.0.0", force=False)
        assert action == "refuse"

    def should_install_on_newer_installed_with_force(self):
        text = "---\nname: test\nresearcher-version: 2.0.0\n---\ncontent"
        action, _ = decide_skill_action(text, "1.0.0", force=True)
        assert action == "install"

    def should_skip_on_equal_version_even_with_force(self):
        text = "---\nname: test\nresearcher-version: 1.0.0\n---\ncontent"
        action, _ = decide_skill_action(text, "1.0.0", force=True)
        assert action == "skip"
