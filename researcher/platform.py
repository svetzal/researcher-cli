"""Platform detection utilities for MLX acceleration on Apple Silicon."""

import platform
import sys


def is_apple_silicon() -> bool:
    return sys.platform == "darwin" and platform.machine() == "arm64"
