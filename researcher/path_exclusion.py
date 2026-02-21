import fnmatch
from pathlib import Path


def is_path_excluded(relative: Path, exclude_patterns: list[str]) -> bool:
    """Return True if any component of the relative path matches any pattern.

    Args:
        relative: A path relative to the repository base directory.
        exclude_patterns: Glob patterns matched against each path component using
            Unix shell-style wildcards (``fnmatch``). A file is excluded if any
            component of its relative path matches any pattern.

    Returns:
        True if the path should be excluded, False otherwise.
    """
    for pattern in exclude_patterns:
        for part in relative.parts:
            if fnmatch.fnmatch(part, pattern):
                return True
    return False
