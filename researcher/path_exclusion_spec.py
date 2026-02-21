from pathlib import Path

from researcher.path_exclusion import is_path_excluded


class DescribeIsPathExcluded:
    def should_return_false_when_no_patterns(self):
        relative = Path("src/module/file.py")

        result = is_path_excluded(relative, [])

        assert result is False

    def should_exclude_matching_directory_component(self):
        relative = Path("node_modules/lodash/index.js")

        result = is_path_excluded(relative, ["node_modules"])

        assert result is True

    def should_exclude_dot_folders_with_wildcard(self):
        relative = Path(".git/config")

        result = is_path_excluded(relative, [".*"])

        assert result is True

    def should_not_exclude_non_matching_paths(self):
        relative = Path("src/app/main.py")

        result = is_path_excluded(relative, ["node_modules", "dist"])

        assert result is False

    def should_exclude_when_any_pattern_matches(self):
        relative = Path("dist/bundle.js")

        result = is_path_excluded(relative, ["node_modules", "dist"])

        assert result is True

    def should_check_each_component_independently(self):
        relative = Path("src/node_modules/dep/file.txt")

        result = is_path_excluded(relative, ["node_modules"])

        assert result is True

    def should_exclude_file_component_matching_pattern(self):
        relative = Path("src/.DS_Store")

        result = is_path_excluded(relative, [".*"])

        assert result is True

    def should_not_match_partial_component_names(self):
        relative = Path("src/my_node_modules_copy/file.txt")

        result = is_path_excluded(relative, ["node_modules"])

        assert result is False
