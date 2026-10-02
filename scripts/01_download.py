#!/usr/bin/env python3
"""Fetch the World Bank's WDI bulk zip and file it under its Last-Modified date.

The bulk zip (databank.worldbank.org/data/download/WDI_CSV.zip) is
overwritten in place whenever the World Bank revises WDI, so each copy is
kept as a release named by the date of its Last-Modified header, in
data/raw/<YYYY-MM-DD>/WDI_CSV.zip. It is accepted only if it has the
Content-Length the server states; MANIFEST.json beside it records the URL,
size, sha256, Last-Modified and ETag. A release already there is not
replaced.

These zips are not published as they are: they hold indicators under
licences that forbid it (see src/wdi_to_parquet/release.py).

    uv run python scripts/01_download.py
    uv run python scripts/01_download.py --adopt path/to/WDI_CSV.zip path/to/headers.txt
"""

import argparse
import email.utils
import hashlib
import json
import shutil
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
URL = "https://databank.worldbank.org/data/download/WDI_CSV.zip"
UA = "wdi-to-parquet/1 (+https://github.com/yuiseki/wdi-to-parquet)"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def file_release(tmp: Path, url: str, headers: dict[str, str]) -> Path:
    """Check tmp against the headers and move it to data/raw/<date>/."""
    length = int(headers["content-length"])
    got = tmp.stat().st_size
    if got != length:
        raise SystemExit(f"{url}: got {got} bytes, the server stated {length}")
    lm = headers["last-modified"]
    version = email.utils.parsedate_to_datetime(lm).date().isoformat()
    d = RAW / version
    if (d / "MANIFEST.json").exists():
        print(f"{version}: already filed, nothing to do")
        return d
    d.mkdir(parents=True, exist_ok=True)
    dest = d / "WDI_CSV.zip"
    shutil.move(tmp, dest)
    manifest = {
        "WDI_CSV.zip": {
            "url": url,
            "bytes": length,
            "sha256": sha256(dest),
            "last_modified": lm,
            "etag": headers.get("etag", ""),
        }
    }
    (d / "MANIFEST.json").write_text(json.dumps(manifest, indent=1))
    print(f"{version}: {length:,} bytes, {lm}")
    return d


def read_headers(path: Path) -> dict[str, str]:
    """The last response block of a curl -D dump (after redirects)."""
    blocks = path.read_text().replace("\r", "").strip().split("\n\n")
    out = {}
    for line in blocks[-1].splitlines()[1:]:
        k, _, v = line.partition(":")
        out[k.strip().lower()] = v.strip()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--adopt", nargs=2, metavar=("ZIP", "HEADERS"),
                    help="file a zip already fetched with curl -D HEADERS")
    a = ap.parse_args()
    if a.adopt:
        zpath, hpath = map(Path, a.adopt)
        file_release(zpath, URL, read_headers(hpath))
        return 0

    RAW.mkdir(parents=True, exist_ok=True)
    tmp = RAW / "WDI_CSV.zip.part"
    req = urllib.request.Request(URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=600) as r, open(tmp, "wb") as f:
        shutil.copyfileobj(r, f, 1 << 20)
        headers = {k.lower(): v for k, v in r.headers.items()}
    file_release(tmp, URL, headers)
    return 0


if __name__ == "__main__":
    sys.exit(main())
