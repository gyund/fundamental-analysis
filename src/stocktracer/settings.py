"""Settings for the stocktracer package."""
import os
from pathlib import Path

from beartype import beartype


@beartype
def get_default_cache_path() -> Path:
    """Get the default path for caching data.

    Returns:
        Path: path to cache data
    """
    return Path(os.getcwd()) / ".stocktracer-cache"


storage_path: Path = get_default_cache_path()
