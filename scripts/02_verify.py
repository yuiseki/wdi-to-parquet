#!/usr/bin/env python3
"""Check every release: what is published equals the World Bank's zip minus the excluded indicators.

For each data/raw/<version>/:
  - the zip has the sha256 in MANIFEST.json
  - the excluded indicators are those whose licence is not allowed in any
    release, read again from every original WDISeries.csv
  - every rebuilt CSV holds exactly the original records minus those of
    excluded indicators, in the same order, and starts with the same BOM
  - data.parquet holds every non-empty value of the original WDICSV.csv
    except the excluded indicators' and nothing else: compared as an
    order-free checksum over (country, indicator, year, value as float.hex),
    computed from the original with Python's csv module and from the
    Parquet with pyarrow
  - year_int of footnotes and series_time equals parse_year of the original text
  - no Parquet and no CSV holds an excluded indicator
  - a plain DuckDB opens every Parquet, and no row group has a bloom filter
"""

import csv
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

import duckdb
import pyarrow.parquet as pq

from wdi_to_parquet.release import excluded_series, parse_value, parse_year, union_excluded

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MASK = (1 << 64) - 1
KEYS = {
    "WDICSV.csv": "Indicator Code",
    "WDISeries.csv": "Series Code",
    "WDIcountry-series.csv": "SeriesCode",
    "WDIfootnote.csv": "SeriesCode",
    "WDIseries-time.csv": "SeriesCode",
    "WDICountry.csv": None,
}


def h64(s: str) -> int:
    return int.from_bytes(hashlib.blake2b(s.encode(), digest_size=8).digest(), "little")


def rows(z: zipfile.ZipFile, name: str):
    with z.open(name) as f:
        yield from csv.reader(io.TextIOWrapper(f, encoding="utf-8-sig", newline=""))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    failures = []

    def check(ok: bool, what: str) -> None:
        print(("ok    " if ok else "FAIL  ") + what, flush=True)
        if not ok:
            failures.append(what)

    dirs = sorted(p for p in (DATA / "raw").iterdir() if (p / "MANIFEST.json").exists())
    labels = {}
    for d in dirs:
        with zipfile.ZipFile(d / "WDI_CSV.zip") as z, z.open("WDISeries.csv") as f:
            labels[d.name] = excluded_series(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig", newline="")))
    union = union_excluded(labels)
    for d in dirs:
        v = d.name
        m = json.loads((d / "MANIFEST.json").read_text())["WDI_CSV.zip"]
        check(sha256(d / "WDI_CSV.zip") == m["sha256"], f"{v}: zip matches MANIFEST.json")
        orig = zipfile.ZipFile(d / "WDI_CSV.zip")
        clean = zipfile.ZipFile(DATA / "csv" / v / "WDI_CSV_redistributable.zip")
        excl = set(union)
        recorded = json.loads((DATA / "parquet" / v / "excluded.json").read_text())
        check(excl == set(recorded["indicators"]) and recorded["releases_considered"] == [x.name for x in dirs],
              f"{v}: the {len(excl)} excluded indicators are the union over {len(dirs)} releases")

        # rebuilt CSVs: original records minus excluded, same order, same BOM
        for name, key in KEYS.items():
            o, c = rows(orig, name), rows(clean, name)
            header = next(o)
            same_header = header == next(c)
            i = header.index(key) if key else None
            want = h_want = h_got = n_got = 0
            for r in o:
                if i is None or r[i] not in excl:
                    want += 1
                    h_want = (h_want * 1000003 + h64("\x1f".join(r))) & MASK
            for r in c:
                n_got += 1
                h_got = (h_got * 1000003 + h64("\x1f".join(r))) & MASK
                if i is not None and r[i] in excl:
                    failures.append(f"{v}: {name} holds an excluded record")
            with orig.open(name) as fo, clean.open(name) as fc:
                same_bom = fo.read(3) == fc.read(3)
            check(same_header and same_bom and want == n_got and h_want == h_got,
                  f"{v}: {name}, {n_got:,} records, the original's minus the excluded, in order")

        # data.parquet against the original WDICSV.csv
        o = rows(orig, "WDICSV.csv")
        header = next(o)
        years = [(j, int(y)) for j, y in enumerate(header) if y.isdigit()]
        n_want = s_want = 0
        for r in o:
            if r[3] in excl:
                continue
            for j, y in years:
                x = parse_value(r[j])
                if x is not None:
                    n_want += 1
                    s_want = (s_want + h64(f"{r[1]}|{r[3]}|{y}|{x.hex()}")) & MASK
        n_got = s_got = 0
        for b in pq.ParquetFile(DATA / "parquet" / v / "data.parquet").iter_batches(1 << 20):
            for cc, ic, y, x in zip(*(b.column(k).to_pylist() for k in range(4)), strict=True):
                n_got += 1
                s_got = (s_got + h64(f"{cc}|{ic}|{y}|{x.hex()}")) & MASK
        check(n_want == n_got and s_want == s_got,
              f"{v}: data.parquet, {n_got:,} values, the same as the original's non-empty cells")

        # derived years
        for name, table in (("WDIfootnote.csv", "footnotes"), ("WDIseries-time.csv", "series_time")):
            o = rows(clean, name)
            header = next(o)
            i = header.index("Year")
            want = sorted(parse_year(r[i]) for r in o)
            got = sorted(duckdb.sql(f"select year_int as year from '{DATA / 'parquet' / v / (table + '.parquet')}'").fetchnumpy()["year"].tolist())
            check(want == got, f"{v}: {table}.year_int equals parse_year of the original Year ({len(got):,} rows)")

        # no excluded indicator anywhere; plain DuckDB; bloom filters
        con = duckdb.connect()
        cols = {"data": "indicator_code", "series": "Series Code", "country_series": "SeriesCode",
                "footnotes": "SeriesCode", "series_time": "SeriesCode"}
        for table in ("data", "countries", "series", "country_series", "footnotes", "series_time"):
            p = DATA / "parquet" / v / f"{table}.parquet"
            n = con.sql(f"select count(*) from '{p}'").fetchone()[0]
            leak = 0
            if table in cols:
                q = ", ".join(f"'{e}'" for e in excl) or "''"
                leak = con.sql(f'select count(*) from \'{p}\' where "{cols[table]}" in ({q})').fetchone()[0]
            bloom = con.sql(f"select count(*) filter (where bloom_filter_offset is not null) from parquet_metadata('{p}')").fetchone()[0]
            check(leak == 0 and bloom == 0 and n > 0,
                  f"{v}: {table}.parquet opens, {n:,} rows, no excluded indicator, no bloom filters")

    if failures:
        print(f"\n{len(failures)} checks failed")
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
