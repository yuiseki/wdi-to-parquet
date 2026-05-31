"""Tests for wdi_to_parquet.fetch — cache interaction, no live network."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from wdi_to_parquet.cache import CacheStore
from wdi_to_parquet.fetch import fetch_indicator_zip

FIXTURES = Path(__file__).parent / "fixtures"


def _make_fixture_zip() -> bytes:
    """Build a minimal zip mimicking the WDI download structure."""
    import io
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.write(FIXTURES / "API_SP.POP.TOTL_fixture.csv",
                 "API_SP.POP.TOTL_fixture.csv")
        zf.write(FIXTURES / "Metadata_Country_fixture.csv",
                 "Metadata_Country_SP.POP.TOTL_fixture.csv")
    return buf.getvalue()


class TestFetchIndicatorZip:
    def test_cache_miss_calls_requests(self, tmp_path):
        store = CacheStore(tmp_path)
        fake_zip = _make_fixture_zip()

        with patch("wdi_to_parquet.fetch.requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200, content=fake_zip
            )
            result = fetch_indicator_zip("SP.POP.TOTL", store)

        mock_get.assert_called_once()
        assert result == fake_zip

    def test_cache_hit_skips_requests(self, tmp_path):
        store = CacheStore(tmp_path)
        fake_zip = _make_fixture_zip()
        store.put("SP.POP.TOTL", fake_zip)

        with patch("wdi_to_parquet.fetch.requests.get") as mock_get:
            result = fetch_indicator_zip("SP.POP.TOTL", store)

        mock_get.assert_not_called()
        assert result == fake_zip

    def test_result_is_written_to_cache(self, tmp_path):
        store = CacheStore(tmp_path)
        fake_zip = _make_fixture_zip()

        with patch("wdi_to_parquet.fetch.requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200, content=fake_zip
            )
            fetch_indicator_zip("SP.POP.TOTL", store)

        assert store.get("SP.POP.TOTL") == fake_zip

    def test_http_error_raises(self, tmp_path):
        store = CacheStore(tmp_path)
        with patch("wdi_to_parquet.fetch.requests.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=404, content=b"")
            mock_get.return_value.raise_for_status.side_effect = Exception("404")
            with pytest.raises(Exception, match="404"):
                fetch_indicator_zip("BAD.CODE", store)

    @pytest.mark.network
    def test_real_api_returns_zip(self, tmp_path):
        """Live network test — skip with -m 'not network'."""
        import io
        import zipfile
        store = CacheStore(tmp_path)
        data = fetch_indicator_zip("SP.POP.TOTL", store)
        assert zipfile.is_zipfile(io.BytesIO(data))
