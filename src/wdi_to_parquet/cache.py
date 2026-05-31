"""Disk cache with TTL for WDI indicator zip files."""

from __future__ import annotations

import time
from pathlib import Path


class CacheStore:
    """Simple file-based cache: one file per indicator, TTL in days."""

    def __init__(self, cache_dir: Path | str, max_age_days: int = 30) -> None:
        self._dir = Path(cache_dir)
        self._max_age_seconds = max_age_days * 86400

    def _path(self, key: str) -> Path:
        return self._dir / f"{key}.zip"

    def get(self, key: str) -> bytes | None:
        path = self._path(key)
        if not path.exists():
            return None
        age = time.time() - path.stat().st_mtime
        if age > self._max_age_seconds:
            return None
        return path.read_bytes()

    def put(self, key: str, data: bytes) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        tmp = self._path(key).with_suffix(".tmp")
        tmp.write_bytes(data)
        tmp.replace(self._path(key))

    @classmethod
    def default(cls, max_age_days: int = 30) -> CacheStore:
        cache_dir = Path.home() / ".cache" / "wdi-to-parquet"
        return cls(cache_dir, max_age_days=max_age_days)
