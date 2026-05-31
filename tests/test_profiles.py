"""Tests for wdi_to_parquet.profiles — indicator sets and year granularities."""

from __future__ import annotations

from wdi_to_parquet.profiles import (
    INDICATORS_BASIC,
    INDICATORS_MINIMUM,
    YEARS_ANNUAL,
    YEARS_QUINQUENNIAL,
    indicators_for_profile,
    years_for_granularity,
)


class TestYearsQuinquennial:
    def test_includes_landmark_years(self):
        assert 1990 in YEARS_QUINQUENNIAL
        assert 2000 in YEARS_QUINQUENNIAL
        assert 2010 in YEARS_QUINQUENNIAL
        assert 2020 in YEARS_QUINQUENNIAL

    def test_includes_2024(self):
        assert 2024 in YEARS_QUINQUENNIAL

    def test_is_sorted(self):
        assert sorted(YEARS_QUINQUENNIAL) == YEARS_QUINQUENNIAL

    def test_reasonable_count(self):
        # 5-year steps from 1990 to 2024 is about 8-10 points
        assert 7 <= len(YEARS_QUINQUENNIAL) <= 12


class TestYearsAnnual:
    def test_starts_at_1990(self):
        assert YEARS_ANNUAL[0] == 1990

    def test_ends_at_2024(self):
        assert YEARS_ANNUAL[-1] == 2024

    def test_is_consecutive(self):
        for a, b in zip(YEARS_ANNUAL, YEARS_ANNUAL[1:], strict=False):
            assert b == a + 1

    def test_annual_longer_than_quinquennial(self):
        assert len(YEARS_ANNUAL) > len(YEARS_QUINQUENNIAL)


class TestIndicatorsMinimum:
    def test_has_population(self):
        assert "SP.POP.TOTL" in INDICATORS_MINIMUM

    def test_has_gdp(self):
        assert "NY.GDP.MKTP.CD" in INDICATORS_MINIMUM

    def test_has_area(self):
        assert "AG.SRF.TOTL.K2" in INDICATORS_MINIMUM

    def test_small_set(self):
        # minimum should stay tight
        assert len(INDICATORS_MINIMUM) <= 8


class TestIndicatorsBasic:
    def test_is_superset_of_minimum(self):
        assert set(INDICATORS_MINIMUM).issubset(set(INDICATORS_BASIC))

    def test_adds_social_indicators(self):
        # life expectancy or literacy or mortality
        social = {"SP.DYN.LE00.IN", "SE.ADT.LITR.ZS", "SH.DYN.MORT"}
        assert social & set(INDICATORS_BASIC), "basic should include social indicators"

    def test_adds_environment(self):
        assert "EN.ATM.CO2E.PC" in INDICATORS_BASIC

    def test_meaningfully_larger(self):
        assert len(INDICATORS_BASIC) >= len(INDICATORS_MINIMUM) + 4


class TestYearsForGranularity:
    def test_quinquennial(self):
        assert years_for_granularity("quinquennial") == YEARS_QUINQUENNIAL

    def test_annual(self):
        assert years_for_granularity("annual") == YEARS_ANNUAL

    def test_unknown_raises(self):
        import pytest
        with pytest.raises(ValueError, match="unknown granularity"):
            years_for_granularity("monthly")


class TestIndicatorsForProfile:
    def test_minimum(self):
        assert indicators_for_profile("minimum") == INDICATORS_MINIMUM

    def test_basic(self):
        assert indicators_for_profile("basic") == INDICATORS_BASIC

    def test_unknown_raises(self):
        import pytest
        with pytest.raises(ValueError, match="unknown profile"):
            indicators_for_profile("full")
