---
license: cc-by-4.0
language:
- en
task_categories:
- tabular-regression
- time-series-forecasting
tags:
- world-bank
- wdi
- development-indicators
- economics
- country-level
size_categories:
- 1M<n<10M
configs:
- config_name: '2026-10-01.data'
  data_files: parquet/2026-10-01/data.parquet
  default: true
- config_name: '2026-10-01.countries'
  data_files: parquet/2026-10-01/countries.parquet
- config_name: '2026-10-01.series'
  data_files: parquet/2026-10-01/series.parquet
- config_name: '2026-10-01.country_series'
  data_files: parquet/2026-10-01/country_series.parquet
- config_name: '2026-10-01.footnotes'
  data_files: parquet/2026-10-01/footnotes.parquet
- config_name: '2026-10-01.series_time'
  data_files: parquet/2026-10-01/series_time.parquet
- config_name: '2026-07-15.data'
  data_files: parquet/2026-07-15/data.parquet
- config_name: '2026-07-15.countries'
  data_files: parquet/2026-07-15/countries.parquet
- config_name: '2026-07-15.series'
  data_files: parquet/2026-07-15/series.parquet
- config_name: '2026-07-15.country_series'
  data_files: parquet/2026-07-15/country_series.parquet
- config_name: '2026-07-15.footnotes'
  data_files: parquet/2026-07-15/footnotes.parquet
- config_name: '2026-07-15.series_time'
  data_files: parquet/2026-07-15/series_time.parquet
- config_name: '2026-04-09.data'
  data_files: parquet/2026-04-09/data.parquet
- config_name: '2026-04-09.countries'
  data_files: parquet/2026-04-09/countries.parquet
- config_name: '2026-04-09.series'
  data_files: parquet/2026-04-09/series.parquet
- config_name: '2026-04-09.country_series'
  data_files: parquet/2026-04-09/country_series.parquet
- config_name: '2026-04-09.footnotes'
  data_files: parquet/2026-04-09/footnotes.parquet
- config_name: '2026-04-09.series_time'
  data_files: parquet/2026-04-09/series_time.parquet
- config_name: '2026-02-25.data'
  data_files: parquet/2026-02-25/data.parquet
- config_name: '2026-02-25.countries'
  data_files: parquet/2026-02-25/countries.parquet
- config_name: '2026-02-25.series'
  data_files: parquet/2026-02-25/series.parquet
- config_name: '2026-02-25.country_series'
  data_files: parquet/2026-02-25/country_series.parquet
- config_name: '2026-02-25.footnotes'
  data_files: parquet/2026-02-25/footnotes.parquet
- config_name: '2026-02-25.series_time'
  data_files: parquet/2026-02-25/series_time.parquet
- config_name: '2025-12-19.data'
  data_files: parquet/2025-12-19/data.parquet
- config_name: '2025-12-19.countries'
  data_files: parquet/2025-12-19/countries.parquet
- config_name: '2025-12-19.series'
  data_files: parquet/2025-12-19/series.parquet
- config_name: '2025-12-19.country_series'
  data_files: parquet/2025-12-19/country_series.parquet
- config_name: '2025-12-19.footnotes'
  data_files: parquet/2025-12-19/footnotes.parquet
- config_name: '2025-12-19.series_time'
  data_files: parquet/2025-12-19/series_time.parquet
- config_name: '2025-07-02.data'
  data_files: parquet/2025-07-02/data.parquet
- config_name: '2025-07-02.countries'
  data_files: parquet/2025-07-02/countries.parquet
- config_name: '2025-07-02.series'
  data_files: parquet/2025-07-02/series.parquet
- config_name: '2025-07-02.country_series'
  data_files: parquet/2025-07-02/country_series.parquet
- config_name: '2025-07-02.footnotes'
  data_files: parquet/2025-07-02/footnotes.parquet
- config_name: '2025-07-02.series_time'
  data_files: parquet/2025-07-02/series_time.parquet
- config_name: '2024-05-30.data'
  data_files: parquet/2024-05-30/data.parquet
- config_name: '2024-05-30.countries'
  data_files: parquet/2024-05-30/countries.parquet
- config_name: '2024-05-30.series'
  data_files: parquet/2024-05-30/series.parquet
- config_name: '2024-05-30.country_series'
  data_files: parquet/2024-05-30/country_series.parquet
- config_name: '2024-05-30.footnotes'
  data_files: parquet/2024-05-30/footnotes.parquet
- config_name: '2024-05-30.series_time'
  data_files: parquet/2024-05-30/series_time.parquet
---

# worldbank-wdi

The World Bank's World Development Indicators (WDI), one subset per release
as the World Bank published it: every value of every indicator for every
economy and year, in long format, with the indicator definitions, the
country table and the footnotes beside it. 74 indicators are left out of
every release because their data is not the World Bank's to license under
CC BY (see Left out).

CC BY 4.0 with the World Bank's mandatory dispute terms (see Licence).

## Releases

The World Bank overwrites its bulk zip in place whenever it revises WDI, and
its data catalogue keeps some of the past zips under dated names
(`WDI_CSV_YYYY_MM_DD.zip`). Each release here is one of those zips, named by
that date; the current zip is named by its Last-Modified date. A release
that vanishes from the World Bank stays here. Analyses should state the
release they used.

| release | values | indicators | economies | years | zip taken | zip bytes |
|---|---:|---:|---:|---|---|---:|
| `2026-10-01` | 8,790,085 | 1,441 | 264 | 1960 to 2025 | databank.worldbank.org/data/download/WDI_CSV.zip | 282,847,680 |
| `2026-07-15` | 8,790,085 | 1,441 | 264 | 1960 to 2025 | WDI_CSV_2026_07_15.zip | 282,845,220 |
| `2026-04-09` | 8,668,470 | 1,429 | 265 | 1960 to 2025 | WDI_CSV_2026_04_09.zip | 280,478,558 |
| `2026-02-25` | 8,814,241 | 1,459 | 265 | 1960 to 2025 | WDI_CSV_2026_02_25.zip | 57,930,154 |
| `2025-12-19` | 8,811,962 | 1,456 | 265 | 1960 to 2024 | WDI_CSV_2025_12_19.zip | 283,432,471 |
| `2025-07-02` | 8,721,690 | 1,458 | 265 | 1960 to 2024 | WDI_CSV_2025_07_02.zip | 282,306,239 |
| `2024-05-30` | 8,221,867 | 1,434 | 265 | 1960 to 2023 | WDI_CSV_2024_05_30.zip | 267,402,945 |

The dated zips are at
`https://datacatalogfiles.worldbank.org/ddh-published/0037712/DR0095335/`.
The data catalogue's `WDI_CSV_2026_10_01.zip` has the same sha256 as the
current zip of 2026-10-01. 2026-07-15 and 2026-10-01 hold the same values;
they differ in the indicator metadata (WDISeries.csv), which is where the
SIPRI indicators got their SIPRI licence back. `raw/<release>/MANIFEST.json`
gives each zip's URL, size, sha256, Last-Modified and ETag.

Older WDI releases exist as Excel zips back to 2005 and through the WDI
Database Archives API back to 1989. They are not here yet.

## Files and columns

Per release:

| file | content |
|---|---|
| `parquet/<release>/data.parquet` | one row per non-empty value: `country_code`, `indicator_code`, `year` (SMALLINT), `value` (DOUBLE), sorted by indicator, country, year |
| `parquet/<release>/countries.parquet` | WDICountry.csv: one row per economy, with Region, Income Group and notes |
| `parquet/<release>/series.parquet` | WDISeries.csv: one row per indicator, with its definition, source and `License Type` |
| `parquet/<release>/country_series.parquet` | WDIcountry-series.csv: notes for an indicator in an economy |
| `parquet/<release>/footnotes.parquet` | WDIfootnote.csv: notes for a value, with `year_int` added |
| `parquet/<release>/series_time.parquet` | WDIseries-time.csv: notes for an indicator in a year, with `year_int` added |
| `parquet/<release>/excluded.json` | the indicators left out, with the release and label that excluded each |
| `csv/<release>/WDI_CSV_redistributable.zip` | the six CSVs of the World Bank's zip without the records of the left-out indicators |

In the metadata tables every column is the text of the CSV, under its
original name. `year_int` is read from `Year` (`YR2004`); the footnotes
also write it with trailing spaces (27,992 rows of 2026-10-01) and in lower
case (`yr2005`, 92 rows), which `year_int` accepts. The column is not named
`year` because DuckDB matches column names without case and would take it
for `Year`.

`countries` includes the aggregates (World, regions, income groups), whose
`Region` is empty: 47 of 264 rows in 2026-10-01. `data` holds their values
too; drop them with
`WHERE country_code IN (SELECT "Country Code" FROM countries WHERE "Region" <> '')`.

In the rebuilt CSVs every record kept is the World Bank's text byte for
byte, quoting and line breaks included; only the left-out records are
missing.

```sql
-- DuckDB, straight off the Hub: population of Japan in each release, 2020
SELECT 'release 2026-10-01' AS r, value
FROM 'hf://datasets/yuiseki/worldbank-wdi/parquet/2026-10-01/data.parquet'
WHERE indicator_code = 'SP.POP.TOTL' AND country_code = 'JPN' AND year = 2020;
```

## Left out

`WDISeries.csv` gives each indicator a `License Type`. An indicator is left
out of every release when any release labels it with anything other than
`CC BY-4.0` or `CC BY 3.0 IGO`, or with nothing. The labels cannot be taken
one release at a time: the source stays the same while the label changes.
The SIPRI military expenditure series are labelled with SIPRI's terms in
2024-05-30 and 2026-10-01 and `CC BY-4.0` in between; IEA energy series and
WDPA protected-area series carry their providers' terms in 2024-05-30 and
`CC BY-4.0` afterwards.

| reason | indicators | examples |
|---|---:|---|
| SIPRI terms: no commercial use; more than 10 percent needs SIPRI's authorisation | 6 | `MS.MIL.XPND.CD`, `MS.MIL.XPRT.KD` |
| provider terms ("Use and distribution of these data are subject to ..."): IEA, WDPA and others | 27 | `EG.ELC.COAL.ZS`, `EN.CO2.TRAN.ZS`, `ER.PTD.TOTL.ZS` |
| CC BY-NC 4.0 (Climate Watch emissions) | 12 | `EN.ATM.CO2E.KT`, `EN.ATM.CO2E.PC` |
| no licence given | 29 | `SE.LPV.PRIM`, `SI.POV.MPUN`, `IC.FRM.BNKL.ZS` |

The full list, with the release and the label behind each, is in
`excluded.json`. When a new release is added the rule is applied over all
releases again, so an indicator restricted by a new release is also removed
from the older ones.

Three indicators are kept under CC BY 3.0 IGO (Women, Business and the Law:
`GD_WBL_OVL_ENF`, `GD_WBL_OVL_LAW`, `GD_WBL_OVL_SFR`).

## Things to know

- 2026-02-25 writes its numbers with at most 11 significant digits (mostly
  10), the other releases with up to 17. In data.parquet this release's
  values are therefore rounded; that is the World Bank's file, not a
  conversion here.
- Values are revised between releases. 5,490,348 of the 8,777,206 values
  that 2025-12-19 and 2026-02-25 share differ, most by the rounding above,
  some by revision.
- The World Bank's zips are not here: they contain the left-out indicators.

## Checked before upload

`scripts/02_verify.py` in the source repository checks each release: the
zip has its recorded sha256; the left-out indicators are the union computed
again from every original WDISeries.csv; every rebuilt CSV holds exactly the
original records minus the left-out ones, in order, with the same BOM;
data.parquet holds every non-empty value of the original WDICSV.csv except
the left-out indicators' (compared as a checksum over country, indicator,
year and the exact float, from the original read with Python's csv module);
`year_int` equals the year read from `Year`; no file holds a left-out
indicator; every Parquet opens in a plain DuckDB and has no bloom filter.

## Licence

The World Bank's data catalogue (https://datacatalog.worldbank.org/public-licenses):

> The World Bank Group makes data publicly available according to open data
> standards and licenses datasets under the Creative Commons Attribution 4.0
> International license (CC-BY 4.0).

and

> All users of these Datasets under the CC-BY 4.0 License also agree to the
> following mandatory terms:

which are dispute terms: mediation under the WIPO Mediation Rules, then, if
not settled within 45 days, arbitration under the UNCITRAL Arbitration Rules
at the World Bank's headquarters in Washington, DC. This is why the licence
above is CC BY 4.0 with an addition, not plain CC BY 4.0.

Attribution, in the World Bank's format: The World Bank: World Development
Indicators: <the indicator's source, from `series.Source`>. The World Bank
does not endorse this copy.

`LICENSE` beside this file says what was changed.
