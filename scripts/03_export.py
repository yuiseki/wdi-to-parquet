#!/usr/bin/env python3
"""Turn each release's bulk zip into redistributable CSVs and Parquet.

For data/raw/<version>/WDI_CSV.zip:

  csv/<version>/WDI_CSV_redistributable.zip
      the six CSVs of the bulk zip with the records of every excluded
      indicator left out. Each kept record is the original text, byte for
      byte, so the files differ from the World Bank's only by the missing
      records.
  parquet/<version>/data.parquet
      one row per non-empty value of WDICSV.csv: country_code,
      indicator_code, year (SMALLINT), value (DOUBLE)
  parquet/<version>/{countries,series,country_series,footnotes,series_time}.parquet
      the other five CSVs, every column as text under its original name;
      footnotes and series_time also get year_int (SMALLINT) from "YR2004" (DuckDB
      matches column names without case, so year would clash with Year)

An indicator is excluded when its "License Type" in WDISeries.csv is not
CC BY 4.0 or CC BY 3.0 IGO (wdi_to_parquet.release). A value that is not a
number stops the run. data/<version>/excluded.json lists what was left out.

    uv run python scripts/03_export.py
"""

import csv
import json
import shutil
import sys
import zipfile
from pathlib import Path

from wdi_to_parquet.release import excluded_series, filter_records

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
WORK = DATA / "work"
BOM = "﻿"

# member -> the column naming the indicator (None: no indicator column)
MEMBERS = {
    "WDICSV.csv": "Indicator Code",
    "WDICountry.csv": None,
    "WDISeries.csv": "Series Code",
    "WDIcountry-series.csv": "SeriesCode",
    "WDIfootnote.csv": "SeriesCode",
    "WDIseries-time.csv": "SeriesCode",
}
TABLES = {
    "WDICountry.csv": "countries",
    "WDISeries.csv": "series",
    "WDIcountry-series.csv": "country_series",
    "WDIfootnote.csv": "footnotes",
    "WDIseries-time.csv": "series_time",
}
NUMBER = r"-?([0-9]+(\.[0-9]*)?|\.[0-9]+)([eE][-+]?[0-9]+)?"
COPY = "(format parquet, compression zstd, row_group_size 100000, write_bloom_filter false)"


def rebuild(src: Path, dst: Path, key: str | None, excluded: set[str]) -> dict:
    if key is None:  # nothing to leave out: the file as it is
        shutil.copyfile(src, dst)
        with open(src, encoding="utf-8-sig", newline="") as f:
            n = sum(1 for _ in csv.reader(f)) - 1
        return {"kept": n, "dropped": 0}
    with open(src, encoding="utf-8", newline="") as f:
        bom = f.read(1) == BOM
        if not bom:
            f.seek(0)
        with open(dst, "w", encoding="utf-8", newline="") as out:
            if bom:
                out.write(BOM)
            kept, dropped = filter_records(f, key, excluded, out)
    return {"kept": kept, "dropped": dropped}


def export(version: str, con) -> None:
    zpath = RAW / version / "WDI_CSV.zip"
    work = WORK / version
    orig, clean = work / "original", work / "clean"
    orig.mkdir(parents=True, exist_ok=True)
    clean.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zpath) as z:
        names = set(z.namelist())
        if names != set(MEMBERS):
            raise SystemExit(f"{version}: members {sorted(names)} differ from {sorted(MEMBERS)}")
        z.extractall(orig)  # CRC checked on read

    with open(orig / "WDISeries.csv", encoding="utf-8-sig", newline="") as f:
        excluded = excluded_series(csv.DictReader(f))
    counts = {m: rebuild(orig / m, clean / m, k, set(excluded)) for m, k in MEMBERS.items()}

    out_csv = DATA / "csv" / version
    out_csv.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_csv / "WDI_CSV_redistributable.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for m in MEMBERS:
            z.write(clean / m, m)

    out_pq = DATA / "parquet" / version
    out_pq.mkdir(parents=True, exist_ok=True)

    def src(m: str) -> str:
        return (f"read_csv('{clean / m}', header = true, all_varchar = true, "
                f"strict_mode = true, encoding = 'utf-8')")

    years = [c for c in con.sql(f"select * from {src('WDICSV.csv')} limit 0").columns
             if c.isdigit()]
    cols = ", ".join(f'"{y}"' for y in years)
    con.execute(f"""
        copy (
          select "Country Code" as country_code, "Indicator Code" as indicator_code,
                 cast(year as smallint) as year,
                 case when regexp_full_match(v, '{NUMBER}') then cast(v as double)
                      else error('WDICSV.csv: not a number: ' || v) end as value
          from (unpivot (select "Country Code", "Indicator Code", {cols} from {src('WDICSV.csv')})
                on {cols} into name year value v)
          where v is not null and v <> ''
          order by indicator_code, country_code, year
        ) to '{out_pq / "data.parquet"}' {COPY}""")

    for m, table in TABLES.items():
        extra = ""
        if table in ("footnotes", "series_time"):
            # as wdi_to_parquet.release.parse_year: trailing spaces and yr2004 occur
            y = "upper(rtrim(\"Year\", ' '))"
            extra = (f", case when regexp_full_match({y}, 'YR[0-9]{{4}}') "
                     f"then cast(substr({y}, 3) as smallint) "
                     f"else error('{m}: Year is not YRnnnn: ' || \"Year\") end as year_int")
        con.execute(f"copy (select *{extra} from {src(m)}) to '{out_pq / (table + '.parquet')}' {COPY}")

    (DATA / "parquet" / version / "excluded.json").write_text(json.dumps(
        {"rule": "License Type in WDISeries.csv is not CC BY-4.0 or CC BY 3.0 IGO",
         "indicators": excluded, "records": counts}, indent=1, ensure_ascii=False))
    n = con.sql(f"select count(*) from '{out_pq / 'data.parquet'}'").fetchone()[0]
    print(f"{version}: {n:,} values, {len(excluded)} indicators excluded", flush=True)


def main() -> int:
    import duckdb

    con = duckdb.connect()
    con.execute("set memory_limit = '16GB'")
    for d in sorted(p for p in RAW.iterdir() if (p / "MANIFEST.json").exists()):
        export(d.name, con)
    return 0


if __name__ == "__main__":
    sys.exit(main())
