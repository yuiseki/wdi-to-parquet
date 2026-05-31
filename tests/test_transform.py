"""Tests for wdi_to_parquet.transform — run without network."""

from __future__ import annotations

from pathlib import Path

import pytest

from wdi_to_parquet.transform import (
    filter_real_countries,
    melt_to_long,
    parse_country_metadata,
    parse_wdi_csv,
)

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def raw_wdi_bytes() -> bytes:
    return (FIXTURES / "API_SP.POP.TOTL_fixture.csv").read_bytes()


@pytest.fixture
def metadata_bytes() -> bytes:
    return (FIXTURES / "Metadata_Country_fixture.csv").read_bytes()


class TestParseWdiCsv:
    def test_skips_four_header_rows(self, raw_wdi_bytes):
        df = parse_wdi_csv(raw_wdi_bytes)
        assert "Country Code" in df.columns
        assert "Indicator Code" in df.columns

    def test_year_columns_present(self, raw_wdi_bytes):
        df = parse_wdi_csv(raw_wdi_bytes)
        assert "2000" in df.columns
        assert "2023" in df.columns

    def test_row_count_includes_aggregates(self, raw_wdi_bytes):
        df = parse_wdi_csv(raw_wdi_bytes)
        # fixture has 6 data rows (JPN, USA, BGD, ARB, WLD, SGP) + possible empty
        assert len(df) >= 4


class TestParseCountryMetadata:
    def test_returns_set_of_iso3(self, metadata_bytes):
        real = parse_country_metadata(metadata_bytes)
        assert isinstance(real, set)
        assert "JPN" in real
        assert "USA" in real

    def test_excludes_aggregates(self, metadata_bytes):
        real = parse_country_metadata(metadata_bytes)
        assert "ARB" not in real
        assert "WLD" not in real

    def test_includes_all_real_countries(self, metadata_bytes):
        real = parse_country_metadata(metadata_bytes)
        assert real == {"JPN", "USA", "BGD", "SGP"}


class TestFilterRealCountries:
    def test_drops_aggregate_rows(self, raw_wdi_bytes, metadata_bytes):
        df = parse_wdi_csv(raw_wdi_bytes)
        real = parse_country_metadata(metadata_bytes)
        filtered = filter_real_countries(df, real)
        assert "ARB" not in filtered["Country Code"].values
        assert "WLD" not in filtered["Country Code"].values

    def test_keeps_real_country_rows(self, raw_wdi_bytes, metadata_bytes):
        df = parse_wdi_csv(raw_wdi_bytes)
        real = parse_country_metadata(metadata_bytes)
        filtered = filter_real_countries(df, real)
        assert set(filtered["Country Code"]) == {"JPN", "USA", "BGD", "SGP"}


class TestMeltToLong:
    def test_output_columns(self, raw_wdi_bytes, metadata_bytes):
        df = parse_wdi_csv(raw_wdi_bytes)
        real = parse_country_metadata(metadata_bytes)
        filtered = filter_real_countries(df, real)
        long = melt_to_long(filtered, indicator="SP.POP.TOTL", years=[2000, 2023])
        assert list(long.columns) == ["iso3", "year", "indicator", "value"]

    def test_year_column_is_int(self, raw_wdi_bytes, metadata_bytes):
        df = parse_wdi_csv(raw_wdi_bytes)
        real = parse_country_metadata(metadata_bytes)
        filtered = filter_real_countries(df, real)
        long = melt_to_long(filtered, indicator="SP.POP.TOTL", years=[2000, 2023])
        assert long["year"].dtype == int

    def test_value_column_is_float(self, raw_wdi_bytes, metadata_bytes):
        df = parse_wdi_csv(raw_wdi_bytes)
        real = parse_country_metadata(metadata_bytes)
        filtered = filter_real_countries(df, real)
        long = melt_to_long(filtered, indicator="SP.POP.TOTL", years=[2000, 2023])
        assert long["value"].dtype == float

    def test_indicator_column_filled(self, raw_wdi_bytes, metadata_bytes):
        df = parse_wdi_csv(raw_wdi_bytes)
        real = parse_country_metadata(metadata_bytes)
        filtered = filter_real_countries(df, real)
        long = melt_to_long(filtered, indicator="SP.POP.TOTL", years=[2000, 2023])
        assert (long["indicator"] == "SP.POP.TOTL").all()

    def test_keeps_only_requested_years(self, raw_wdi_bytes, metadata_bytes):
        df = parse_wdi_csv(raw_wdi_bytes)
        real = parse_country_metadata(metadata_bytes)
        filtered = filter_real_countries(df, real)
        long = melt_to_long(filtered, indicator="SP.POP.TOTL", years=[2000])
        assert set(long["year"]) == {2000}

    def test_drops_nan_values(self, raw_wdi_bytes, metadata_bytes):
        df = parse_wdi_csv(raw_wdi_bytes)
        real = parse_country_metadata(metadata_bytes)
        filtered = filter_real_countries(df, real)
        long = melt_to_long(filtered, indicator="SP.POP.TOTL", years=[2000, 2023])
        assert long["value"].notna().all()

    def test_japan_2023_population(self, raw_wdi_bytes, metadata_bytes):
        df = parse_wdi_csv(raw_wdi_bytes)
        real = parse_country_metadata(metadata_bytes)
        filtered = filter_real_countries(df, real)
        long = melt_to_long(filtered, indicator="SP.POP.TOTL", years=[2023])
        jpn = long[(long["iso3"] == "JPN") & (long["year"] == 2023)]
        assert len(jpn) == 1
        assert jpn.iloc[0]["value"] == pytest.approx(124516650)
