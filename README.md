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

## The worldbank-wdi dataset

Dataset: https://huggingface.co/datasets/yuiseki/worldbank-wdi

Besides the CLI above, this repository builds the whole of WDI, every
release it can get, as a dataset on the Hugging Face Hub: each World Bank
bulk zip becomes one release, with its values in long-format Parquet, its
metadata tables, and its CSVs rebuilt without the indicators that are not
the World Bank's to license under CC BY. The card (`data/README.md`) says
what is in it and why 74 indicators are left out.

```
scripts/SOURCES.json     the current bulk zip and the dated zips of the data catalogue
scripts/01_download.py   fetches each zip, files it under data/raw/<YYYY-MM-DD>/ with MANIFEST.json
scripts/03_export.py     zip -> csv/<release>/ (rebuilt CSVs) and parquet/<release>/
scripts/02_verify.py     checks every release against the original zip
scripts/publish.py       dry run; --push uploads to the Hub
src/wdi_to_parquet/release.py   the licence rule, the record filter, the value and year parsers

data/README.md, LICENSE, provenance.yaml   the card and its companions, uploaded as they are
data/raw/, csv/, parquet/, work/           generated; raw/ holds the World Bank's zips, never uploaded
```

```sh
uv run python scripts/01_download.py
uv run python scripts/03_export.py
uv run python scripts/02_verify.py
uv run python scripts/publish.py
```

A new release: add its dated URL to `SOURCES.json` (the current zip is
picked up by itself), declare its six subsets in `data/README.md`, and run
the four steps. The licence rule is applied over all releases, so the
export rewrites the older releases too; upload them all again.

Run the tests with `uv run python -m pytest`. A plain `uv run pytest` can
pick up a pytest installed outside the project, which cannot import the
package.

## Tests

```bash
uv run python -m pytest                   # all tests
uv run python -m pytest -m "not network"  # skip network
uv run python -m pytest -m network        # only network tests (requires internet)
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