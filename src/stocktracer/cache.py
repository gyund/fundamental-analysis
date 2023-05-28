"""This module takes care of managing caching configuration."""
import atexit
import hashlib
import os
from datetime import timedelta

from diskcache import Cache
from requests_cache import CachedSession, SQLiteCache

from stocktracer import settings

settings.storage_path.mkdir(parents=True, exist_ok=True)

results = Cache(directory=settings.storage_path / "results", tag_index=True)


sec_data = CachedSession(
    "data",
    backend=SQLiteCache(db_path=settings.storage_path / "data"),
    serializer="pickle",
    expire_after=timedelta(days=365 * 5),
    stale_if_error=True,
)
sec_tickers = CachedSession(
    "tickers",
    backend=SQLiteCache(db_path=settings.storage_path / "tickers"),
    expire_after=timedelta(days=365),
    stale_if_error=True,
)


dir_name = os.path.dirname(__file__)
opened_file = open(os.path.join(dir_name, "collector/sec.py"))
readFile = opened_file.read()
opened_file.close()

SEC_FILE_HASH = hashlib.sha256(readFile.encode()).hexdigest()

if SEC_FILE_HASH != results.get("sec_file_hash"):
    results.evict(tag="sec")
    results.evict(tag="results")


def update_modified_file_cache() -> None:
    """Update the cache that keeps track of when files are modified."""
    results.set("sec_file_hash", SEC_FILE_HASH)


atexit.register(update_modified_file_cache)
