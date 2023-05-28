"""This module takes care of managing caching configuration."""
import atexit
import hashlib
import os
from datetime import timedelta
from pathlib import Path

from beartype import beartype
from diskcache import Cache
from platformdirs import user_cache_dir
from requests_cache import CachedSession, SQLiteCache


@beartype
def get_cache_dir() -> Path:
    """Get the cache directory used by stocktracer.

    Users can customize this directory on all systems using `STOCKTRACER_CACHE_DIR`
    environment variable. By default, the cache directory is the user cache directory
    under the stocktracer application.

    This result is immediately set to a constant `stocktracer.cache.CACHE_DIR` as to avoid
    repeated calls.

    Returns:
        Path: path to the cache directory
    """
    default_cache_dir = user_cache_dir("stocktracer")
    cache_dir = Path(os.environ.get("STOCKTRACER_CACHE_DIR", default_cache_dir))
    return cache_dir


CACHE_DIR = get_cache_dir()
CACHE_DIR.mkdir(parents=True, exist_ok=True)

results = Cache(directory=CACHE_DIR / "results", tag_index=True)


sec_data = CachedSession(
    "data",
    backend=SQLiteCache(db_path=CACHE_DIR / "data"),
    serializer="pickle",
    expire_after=timedelta(days=365 * 5),
    stale_if_error=True,
)
sec_tickers = CachedSession(
    "tickers",
    backend=SQLiteCache(db_path=CACHE_DIR / "tickers"),
    expire_after=timedelta(days=365),
    stale_if_error=True,
)


dir_name = os.path.dirname(__file__)
with open(os.path.join(dir_name, "collector/sec.py"), encoding="utf8") as opened_file:
    readFile = opened_file.read()


SEC_FILE_HASH = hashlib.sha256(readFile.encode()).hexdigest()

if SEC_FILE_HASH != results.get("sec_file_hash"):
    results.evict(tag="sec")
    results.evict(tag="results")


def update_modified_file_cache() -> None:
    """Update the cache that keeps track of when files are modified."""
    results.set("sec_file_hash", SEC_FILE_HASH)


atexit.register(update_modified_file_cache)
