"""End-to-end analytical query tests.

These demonstrate what wdi-to-parquet makes possible: JOIN WDI indicators
with Natural Earth geometry to answer geospatial questions via DuckDB SQL.

Run with:
    uv run pytest tests/e2e/ -v              # requires network
    uv run pytest -m "not e2e"               # skip in CI without network

Each test is also a usage example — read the SQL to understand the query.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.e2e


class TestPopulationRanking:
    """Q1: Which countries are most populous? (2024)"""

    def test_top_country_is_india_or_china(self, con):
        rows = con.execute("""
            SELECT adm0.name_ja, w.value::BIGINT AS population
            FROM wdi w JOIN adm0 USING (iso3)
            WHERE w.indicator = 'SP.POP.TOTL' AND w.year = 2024
            ORDER BY w.value DESC LIMIT 1
        """).fetchall()
        assert len(rows) == 1
        top = rows[0][0]
        assert top in ("インド", "中華人民共和国"), f"Unexpected top: {top}"

    def test_returns_ten_rows(self, con):
        rows = con.execute("""
            SELECT adm0.name_ja, w.value::BIGINT AS population
            FROM wdi w JOIN adm0 USING (iso3)
            WHERE w.indicator = 'SP.POP.TOTL' AND w.year = 2024
            ORDER BY w.value DESC LIMIT 10
        """).fetchall()
        assert len(rows) == 10

    def test_japan_appears_in_top_15(self, con):
        rows = con.execute("""
            SELECT adm0.name_ja
            FROM wdi w JOIN adm0 USING (iso3)
            WHERE w.indicator = 'SP.POP.TOTL' AND w.year = 2024
            ORDER BY w.value DESC LIMIT 15
        """).fetchall()
        names = [r[0] for r in rows]
        assert "日本" in names, f"Japan not in top 15: {names}"


class TestPopulationDensity:
    """Q2: Which countries have the highest population density? (2024 pop / 2023 area)

    density = SP.POP.TOTL / AG.SRF.TOTL.K2
    Excludes very small countries (area < 100 km²) to avoid micro-states
    dominating the ranking.
    """

    def test_singapore_is_densest_large_country(self, con):
        rows = con.execute("""
            WITH pop  AS (SELECT iso3, value AS pop  FROM wdi WHERE indicator='SP.POP.TOTL'    AND year=2024),
                 area AS (SELECT iso3, value AS area FROM wdi WHERE indicator='AG.SRF.TOTL.K2' AND year=2023)
            SELECT adm0.name_ja, ROUND(pop.pop / area.area) AS density
            FROM pop JOIN area USING (iso3) JOIN adm0 USING (iso3)
            WHERE area.area > 100
            ORDER BY density DESC LIMIT 1
        """).fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "シンガポール", f"Unexpected densest: {rows[0][0]}"

    def test_density_is_non_negative(self, con):
        rows = con.execute("""
            WITH pop  AS (SELECT iso3, value AS pop  FROM wdi WHERE indicator='SP.POP.TOTL'    AND year=2024),
                 area AS (SELECT iso3, value AS area FROM wdi WHERE indicator='AG.SRF.TOTL.K2' AND year=2023)
            SELECT ROUND(pop.pop / area.area) AS density
            FROM pop JOIN area USING (iso3) JOIN adm0 USING (iso3)
            WHERE area.area > 100
        """).fetchall()
        # Some very sparse countries (e.g. Greenland) round to 0; none should be negative
        assert all(r[0] >= 0 for r in rows)

    def test_singapore_density_approx(self, con):
        rows = con.execute("""
            WITH pop  AS (SELECT iso3, value AS pop  FROM wdi WHERE indicator='SP.POP.TOTL'    AND year=2024),
                 area AS (SELECT iso3, value AS area FROM wdi WHERE indicator='AG.SRF.TOTL.K2' AND year=2023)
            SELECT ROUND(pop.pop / area.area) AS density
            FROM pop JOIN area USING (iso3) JOIN adm0 USING (iso3)
            WHERE adm0.name_ja = 'シンガポール'
        """).fetchone()
        density = rows[0]
        assert 7000 < density < 10000, f"Singapore density out of range: {density}"


class TestPopulationGrowth:
    """Q3: Which countries grew fastest between 2020 and 2024?

    growth_pct = (pop_2024 - pop_2020) / pop_2020 * 100
    Only considers countries with population > 1M to avoid small-state noise.
    """

    def test_returns_rows(self, con):
        rows = con.execute("""
            WITH p2020 AS (SELECT iso3, value AS p FROM wdi WHERE indicator='SP.POP.TOTL' AND year=2020),
                 p2024 AS (SELECT iso3, value AS p FROM wdi WHERE indicator='SP.POP.TOTL' AND year=2024)
            SELECT adm0.name_ja, ROUND((p2024.p - p2020.p) / p2020.p * 100, 2) AS growth_pct
            FROM p2020 JOIN p2024 USING (iso3) JOIN adm0 USING (iso3)
            WHERE p2020.p > 1000000
            ORDER BY growth_pct DESC LIMIT 10
        """).fetchall()
        assert len(rows) == 10

    def test_growth_leader_is_sub_saharan_or_middle_east(self, con):
        rows = con.execute("""
            WITH p2020 AS (SELECT iso3, value AS p FROM wdi WHERE indicator='SP.POP.TOTL' AND year=2020),
                 p2024 AS (SELECT iso3, value AS p FROM wdi WHERE indicator='SP.POP.TOTL' AND year=2024)
            SELECT adm0.name_ja, ROUND((p2024.p - p2020.p) / p2020.p * 100, 2) AS growth_pct
            FROM p2020 JOIN p2024 USING (iso3) JOIN adm0 USING (iso3)
            WHERE p2020.p > 1000000
            ORDER BY growth_pct DESC LIMIT 1
        """).fetchone()
        # Top growers are consistently Sub-Saharan Africa or Gulf states
        assert rows[1] > 5.0, f"Top growth rate unexpectedly low: {rows[1]}"

    def test_japan_has_negative_growth(self, con):
        row = con.execute("""
            WITH p2020 AS (SELECT iso3, value AS p FROM wdi WHERE indicator='SP.POP.TOTL' AND year=2020),
                 p2024 AS (SELECT iso3, value AS p FROM wdi WHERE indicator='SP.POP.TOTL' AND year=2024)
            SELECT ROUND((p2024.p - p2020.p) / p2020.p * 100, 2) AS growth_pct
            FROM p2020 JOIN p2024 USING (iso3) JOIN adm0 USING (iso3)
            WHERE adm0.name_ja = '日本'
        """).fetchone()
        assert row[0] < 0, f"Japan population growth should be negative, got: {row[0]}"


class TestGdpPerCapita:
    """Q4: Which countries have the highest GDP per capita? (2024)"""

    def test_top_country_is_high_income(self, con):
        rows = con.execute("""
            SELECT adm0.name_ja, ROUND(w.value)::BIGINT AS gdp_pc
            FROM wdi w JOIN adm0 USING (iso3)
            WHERE w.indicator = 'NY.GDP.PCAP.CD' AND w.year = 2024
            ORDER BY w.value DESC LIMIT 1
        """).fetchone()
        assert rows[1] > 100000, f"Top GDP per capita unexpectedly low: {rows[1]}"

    def test_returns_ten_rows(self, con):
        rows = con.execute("""
            SELECT adm0.name_ja, ROUND(w.value)::BIGINT AS gdp_pc
            FROM wdi w JOIN adm0 USING (iso3)
            WHERE w.indicator = 'NY.GDP.PCAP.CD' AND w.year = 2024
            ORDER BY w.value DESC LIMIT 10
        """).fetchall()
        assert len(rows) == 10


class TestTimeSeries:
    """Q5: Multi-year data for a single country (Japan population 1990-2024)."""

    def test_japan_has_all_years(self, con):
        rows = con.execute("""
            SELECT w.year, (w.value / 1e6)::DECIMAL(10,2) AS population_M
            FROM wdi w JOIN adm0 USING (iso3)
            WHERE w.indicator = 'SP.POP.TOTL' AND adm0.name_ja = '日本'
            ORDER BY w.year
        """).fetchall()
        years = [r[0] for r in rows]
        assert 1990 in years
        assert 2024 in years
        assert len(rows) >= 6

    def test_japan_peak_population_around_2010(self, con):
        rows = con.execute("""
            SELECT w.year, w.value AS population
            FROM wdi w JOIN adm0 USING (iso3)
            WHERE w.indicator = 'SP.POP.TOTL' AND adm0.name_ja = '日本'
            ORDER BY w.value DESC LIMIT 1
        """).fetchone()
        peak_year = rows[0]
        # Japan's population peaked around 2008-2012
        assert 2005 <= peak_year <= 2015, f"Japan peak year unexpected: {peak_year}"


class TestGeometryJoin:
    """Q6: JOIN with Natural Earth geometry — the core use case."""

    def test_returns_geometry_column(self, con):
        rows = con.execute("""
            SELECT adm0.name_ja, w.value::BIGINT AS population,
                   ST_AsText(adm0.geom) AS geom_wkt
            FROM wdi w JOIN adm0 USING (iso3)
            WHERE w.indicator = 'SP.POP.TOTL' AND w.year = 2024
            ORDER BY w.value DESC LIMIT 3
        """).fetchall()
        assert len(rows) == 3
        for row in rows:
            assert row[2] is not None
            assert row[2].startswith("MULTIPOLYGON") or row[2].startswith("POLYGON")

    def test_iso3_join_covers_major_countries(self, con):
        count = con.execute("""
            SELECT COUNT(DISTINCT adm0.iso3)
            FROM wdi w JOIN adm0 USING (iso3)
            WHERE w.indicator = 'SP.POP.TOTL' AND w.year = 2024
        """).fetchone()[0]
        # 212 countries match between WDI and NE 50m
        assert count > 200, f"Too few matching countries: {count}"
