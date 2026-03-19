"""Platform detection utilities for MLX acceleration on Apple Silicon."""

import platform
import sys


def is_apple_silicon() -> bool:
    """Return True when running on macOS with an Apple Silicon (arm64) chip."""
    return sys.platform == "darwin" and platform.machine() == "arm64"
