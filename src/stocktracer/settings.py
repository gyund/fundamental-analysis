import os

from beartype import beartype
from pathlib import Path


@beartype
def get_default_cache_path() -> Path:
    """Get the default path for caching data.

    Returns:
        Path: path to cache data
    """
    return Path(os.getcwd()) / ".ticker-cache"


storage_path: Path = get_default_cache_path()
