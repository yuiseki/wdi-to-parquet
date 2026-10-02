"""Build a redistributable WDI release from the World Bank's bulk zip.

The bulk zip carries a licence per indicator in WDISeries.csv ("License
Type"). Indicators under CC BY 4.0 or CC BY 3.0 IGO are kept; any other
licence, such as SIPRI's terms (no commercial use, no use of more than 10
percent without SIPRI's authorisation), excludes the indicator from
everything published: its values, its metadata rows and its footnotes.
"""

from __future__ import annotations

import csv
import math
import re
from collections.abc import Iterable, Iterator
from typing import TextIO

ALLOWED_LICENCES = {"CC BY-4.0", "CC BY 3.0 IGO"}

_NUMBER = re.compile(r"-?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?")
_YEAR = re.compile(r"YR(\d{4})")


def excluded_series(rows: Iterable[dict[str, str]]) -> dict[str, str]:
    """Series code -> licence text, for every series whose licence is not allowed."""
    out = {}
    for row in rows:
        if "License Type" not in row:
            raise ValueError("WDISeries has no License Type column; cannot tell what may be redistributed")
        lic = (row["License Type"] or "").strip()
        if lic not in ALLOWED_LICENCES:
            out[row["Series Code"]] = lic
    return out


def parse_value(text: str) -> float | None:
    """A WDI cell: empty is None, a decimal number is a float, anything else stops."""
    if text == "":
        return None
    if not _NUMBER.fullmatch(text):
        raise ValueError(f"not a number: {text!r}")
    v = float(text)
    if not math.isfinite(v):
        raise ValueError(f"not a finite number: {text!r}")
    return v


def parse_year(text: str) -> int:
    """The Year column of the footnote files: YR2004, also with trailing spaces or as yr2004."""
    m = _YEAR.fullmatch(text.rstrip(" ").upper())
    if not m:
        raise ValueError(f"not a YRnnnn year: {text!r}")
    return int(m.group(1))


class _Tap:
    """Hands lines to csv.reader and remembers the raw text of each record."""

    def __init__(self, f: TextIO):
        self._f = f
        self._buf: list[str] = []

    def __iter__(self) -> Iterator[str]:
        return self

    def __next__(self) -> str:
        line = next(self._f)
        self._buf.append(line)
        return line

    def take(self) -> str:
        raw, self._buf = "".join(self._buf), []
        return raw


def filter_records(src: TextIO, key: str, excluded: set[str], out: TextIO) -> tuple[int, int]:
    """Copy src to out, leaving out records whose key column is in excluded.

    Kept records are written as the raw text they had, quoting and line
    breaks included, so a file with nothing excluded comes out unchanged.
    Returns (kept, dropped).
    """
    tap = _Tap(src)
    reader = csv.reader(tap)
    header = next(reader)
    if key not in header:
        raise ValueError(f"no {key} column in {header[:6]}")
    i = header.index(key)
    out.write(tap.take())
    kept = dropped = 0
    for row in reader:
        raw = tap.take()
        if row[i] in excluded:
            dropped += 1
        else:
            out.write(raw)
            kept += 1
    return kept, dropped
