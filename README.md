# wdi-to-parquet

Convert [World Bank WDI](https://data.worldbank.org/indicator) indicators to
long-format **Parquet** for analytical SQL queries with DuckDB.

```sql
-- Population density (2023)
WITH pop  AS (SELECT iso3, value AS population FROM wdi WHERE indicator='SP.POP.TOTL' AND year=2023),
     area AS (SELECT iso3, value AS area_km2   FROM wdi WHERE indicator='AG.SRF.TOTL.K2' AND year=2020)
SELECT adm0.name_ja, ROUND(pop.population / area.area_km2) AS density
FROM pop JOIN area USING (iso3)
JOIN read_parquet('https://z.yuiseki.net/static/natural-earth/ne_50m_admin_0_countries.parquet') AS adm0
  ON adm0.iso_a3 = pop.iso3
WHERE area.area_km2 > 100
ORDER BY density DESC LIMIT 10;
-- → シンガポール 8129, 香港 6789, バーレーン 2009 ...
```

## Output schema

```
iso3       VARCHAR  — ISO 3166-1 alpha-3 country code
year       INTEGER  — calendar year
indicator  VARCHAR  — WDI indicator code (e.g. SP.POP.TOTL)
value      DOUBLE   — indicator value
```

## Install

```bash
uv sync
```

## Usage

```bash
# default: 6 indicators x 8 years -> wdi_indicators.parquet
uv run wdi-to-parquet

# custom indicators and output path
uv run wdi-to-parquet \
  --indicators SP.POP.TOTL NY.GDP.PCAP.CD EN.ATM.CO2E.PC \
  --years 2000 2010 2020 2023 \
  --output /data/www/html/static/worldbank/wdi_indicators.parquet

# force re-download (bypass cache)
uv run wdi-to-parquet --force-refresh
```

Downloaded zips are cached at `~/.cache/wdi-to-parquet/` for 30 days by default.
Override with `--cache-dir` and `--max-age-days`.

## Default indicators

| Code | Description |
|------|-------------|
| SP.POP.TOTL | Population, total |
| SP.POP.GROW | Population growth (annual %) |
| NY.GDP.MKTP.CD | GDP (current US$) |
| NY.GDP.PCAP.CD | GDP per capita (current US$) |
| AG.SRF.TOTL.K2 | Surface area (sq. km) |
| SP.URB.TOTL.IN.ZS | Urban population (% of total) |

## Tests

```bash
uv run pytest                   # all tests (skips network tests)
uv run pytest -m "not network"  # explicitly skip network
uv run pytest -m network        # only network tests (requires internet)
```

## Design notes

- **Long format**: `(iso3, year, indicator, value)` — DuckDB `WHERE indicator = '...'`
  で任意指標をオンデマンドに引き出せる。`PIVOT` で横展開も可能。
- **Disk cache with TTL**: 一度ダウンロードした WDI zip は `~/.cache/wdi-to-parquet/`
  に保存され、デフォルト 30 日間再利用される。
- **Aggregate regions excluded**: `Metadata_Country` の `Region` が空の行
  (Arab World, World 等) はフィルタで除外される。
- **JOIN with geometry**: Natural Earth 50m GeoParquet と `iso3 = iso_a3` で
  JOIN して地図可視化・DuckDB Spatial クエリが可能。