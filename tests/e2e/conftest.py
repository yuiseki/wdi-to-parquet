"""Session-scoped fixtures for e2e tests.

The WDI parquet is built once per pytest session into a fixed path under
~/.cache/wdi-to-parquet/e2e_test.parquet so it survives across runs.
The underlying WDI zip files are also cached there (30-day TTL), so after
the first run only the parquet assembly step is repeated.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import pytest

from wdi_to_parquet.cache import CacheStore
from wdi_to_parquet.fetch import fetch_indicator_zip
from wdi_to_parquet.transform import process_zip

E2E_CACHE = Path.home() / ".cache" / "wdi-to-parquet"
E2E_PARQUET = E2E_CACHE / "e2e_test.parquet"

# Minimal indicator set for e2e: covers all query types in test_queries.py
E2E_INDICATORS = [
    "SP.POP.TOTL",      # population — Q1, Q3, Q5, Q6
    "AG.SRF.TOTL.K2",   # surface area — Q2 (density)
    "NY.GDP.PCAP.CD",   # GDP per capita — Q4
]
E2E_YEARS = [1990, 1995, 2000, 2005, 2010, 2015, 2020, 2023]

NE_50M = "https://z.yuiseki.net/static/natural-earth/ne_50m_admin_0_countries.parquet"


@pytest.fixture(scope="session")
def wdi_parquet(pytestconfig) -> Path:
    """Return path to the e2e WDI parquet, building it if needed.

    Uses the shared CacheStore (30-day TTL for WDI zips).
    The assembled parquet is rebuilt each session (fast: just concat + write).
    """
    cache = CacheStore(E2E_CACHE, max_age_days=30)
    frames: list[pd.DataFrame] = []
    for indicator in E2E_INDICATORS:
        zip_bytes = fetch_indicator_zip(indicator, cache)
        df = process_zip(zip_bytes, indicator=indicator, years=E2E_YEARS)
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    E2E_CACHE.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(E2E_PARQUET, index=False, compression="zstd")
    return E2E_PARQUET


@pytest.fixture(scope="session")
def con(wdi_parquet) -> duckdb.DuckDBPyConnection:
    """DuckDB connection with wdi and adm0 views pre-registered."""
    c = duckdb.connect(":memory:")
    c.execute("INSTALL spatial; LOAD spatial;")
    c.execute(f"CREATE VIEW wdi AS SELECT * FROM read_parquet('{wdi_parquet}')")
    c.execute(
        f"CREATE VIEW adm0 AS "
        f"SELECT iso_a3 AS iso3, name, name_ja, geometry AS geom "
        f"FROM read_parquet('{NE_50M}')"
    )
    return c
