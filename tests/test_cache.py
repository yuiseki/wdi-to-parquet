"""Tests for wdi_to_parquet.cache — disk cache with TTL, no network."""

from __future__ import annotations

from wdi_to_parquet.cache import CacheStore


class TestCacheStore:
    def test_miss_returns_none(self, tmp_path):
        store = CacheStore(tmp_path)
        assert store.get("SP.POP.TOTL") is None

    def test_put_then_get_returns_bytes(self, tmp_path):
        store = CacheStore(tmp_path)
        store.put("SP.POP.TOTL", b"hello world")
        result = store.get("SP.POP.TOTL")
        assert result == b"hello world"

    def test_cache_file_created(self, tmp_path):
        store = CacheStore(tmp_path)
        store.put("NY.GDP.MKTP.CD", b"data")
        assert (tmp_path / "NY.GDP.MKTP.CD.zip").exists()

    def test_fresh_cache_hit(self, tmp_path):
        store = CacheStore(tmp_path, max_age_days=30)
        store.put("SP.POP.TOTL", b"fresh")
        assert store.get("SP.POP.TOTL") == b"fresh"

    def test_expired_cache_returns_none(self, tmp_path):
        store = CacheStore(tmp_path, max_age_days=0)
        store.put("SP.POP.TOTL", b"stale")
        # max_age_days=0 means any file is immediately stale
        assert store.get("SP.POP.TOTL") is None

    def test_different_indicators_independent(self, tmp_path):
        store = CacheStore(tmp_path)
        store.put("SP.POP.TOTL", b"pop")
        store.put("NY.GDP.MKTP.CD", b"gdp")
        assert store.get("SP.POP.TOTL") == b"pop"
        assert store.get("NY.GDP.MKTP.CD") == b"gdp"

    def test_put_overwrites(self, tmp_path):
        store = CacheStore(tmp_path)
        store.put("SP.POP.TOTL", b"old")
        store.put("SP.POP.TOTL", b"new")
        assert store.get("SP.POP.TOTL") == b"new"

    def test_cache_dir_created_if_missing(self, tmp_path):
        nested = tmp_path / "a" / "b" / "c"
        store = CacheStore(nested)
        store.put("X", b"y")
        assert nested.exists()
