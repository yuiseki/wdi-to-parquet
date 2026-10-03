"""Tests for building a redistributable WDI release from the bulk zip."""

import io

import pytest

from wdi_to_parquet.release import (
    ALLOWED_LICENCES,
    excluded_series,
    filter_records,
    parse_value,
    parse_year,
    union_excluded,
    version_from_url,
)

SIPRI = (
    "SIPRI terms and conditions: Use and distribution of these data are subject to "
    "Stockholm International Peace Research Institute (SIPRI) terms and conditions."
)


def test_allowed_licences_are_the_two_cc_by_spellings_in_wdi():
    assert {"CC BY-4.0", "CC BY 3.0 IGO"} == ALLOWED_LICENCES


def test_excluded_series_keeps_cc_by_and_drops_everything_else():
    rows = [
        {"Series Code": "SP.POP.TOTL", "License Type": "CC BY-4.0"},
        {"Series Code": "XX.IGO", "License Type": "CC BY 3.0 IGO"},
        {"Series Code": "MS.MIL.XPND.CD", "License Type": SIPRI},
        {"Series Code": "XX.EMPTY", "License Type": ""},
    ]
    assert excluded_series(rows) == {"MS.MIL.XPND.CD": SIPRI, "XX.EMPTY": ""}


def test_excluded_series_without_a_licence_column_stops():
    # older releases may lack the column; guessing would hide restricted data
    with pytest.raises(ValueError, match="License Type"):
        excluded_series([{"Series Code": "SP.POP.TOTL"}])


@pytest.mark.parametrize(
    "text,expected",
    [("11.494704278406504", 11.494704278406504), ("-3", -3.0), ("1.5e-05", 1.5e-05), ("0", 0.0)],
)
def test_parse_value_reads_numbers(text, expected):
    assert parse_value(text) == expected


def test_parse_value_empty_is_none():
    assert parse_value("") is None


@pytest.mark.parametrize("text", ["..", "n/a", "1,000", "nan", "inf"])
def test_parse_value_rejects_what_is_not_a_number(text):
    with pytest.raises(ValueError):
        parse_value(text)


def test_parse_year_reads_the_yr_prefix():
    assert parse_year("YR2004") == 2004


@pytest.mark.parametrize("text", ["YR2011    ", "yr2005", "yr2006    "])
def test_parse_year_reads_the_spellings_wdi_footnotes_use(text):
    # 2026-10-01 WDIfootnote.csv: 27,992 rows with trailing spaces, 92 in lower case
    assert parse_year(text) in (2005, 2006, 2011)


@pytest.mark.parametrize("text", ["2004", "YR", "YR20O4", "Y R2004", "YR 2004"])
def test_parse_year_rejects_other_forms(text):
    with pytest.raises(ValueError):
        parse_year(text)


CSV = (
    'Series Code,Topic\r\n'
    '"SP.POP.TOTL","Health: a\r\nline break"\r\n'
    '"MS.MIL.XPND.CD","Public Sector"\r\n'
    '"NY.GDP.MKTP.CD",\r\n'
)


def run(text, excluded, key="Series Code"):
    out = io.StringIO(newline="")
    kept, dropped = filter_records(io.StringIO(text, newline=""), key, excluded, out)
    return out.getvalue(), kept, dropped


def test_filter_records_with_nothing_excluded_is_byte_identical():
    got, kept, dropped = run(CSV, set())
    assert got == CSV
    assert (kept, dropped) == (3, 0)


def test_filter_records_drops_only_the_excluded_record_and_keeps_line_breaks():
    got, kept, dropped = run(CSV, {"MS.MIL.XPND.CD"})
    assert got == CSV.replace('"MS.MIL.XPND.CD","Public Sector"\r\n', "")
    assert (kept, dropped) == (2, 1)


def test_filter_records_without_the_key_column_stops():
    with pytest.raises(ValueError, match="SeriesCode"):
        run(CSV, set(), key="SeriesCode")


@pytest.mark.parametrize(
    "url,version",
    [
        ("https://datacatalogfiles.worldbank.org/ddh-published/0037712/DR0095335/WDI_CSV_2026_04_09.zip", "2026-04-09"),
        ("https://databank.worldbank.org/data/download/WDI_CSV.zip", None),
        ("https://example.org/WDI_CSV_2026_4_9.zip", None),
    ],
)
def test_version_from_url_reads_the_date_in_the_file_name(url, version):
    assert version_from_url(url) == version


def test_union_excluded_takes_every_series_any_release_restricts():
    per_release = {
        "2026-07-15": {},
        "2026-10-01": {"MS.MIL.XPND.CD": SIPRI},
        "2024-05-30": {"MS.MIL.XPND.CD": "Use and distribution ...", "SE.LPV.PRIM": ""},
    }
    assert union_excluded(per_release) == {
        "MS.MIL.XPND.CD": {"2024-05-30": "Use and distribution ...", "2026-10-01": SIPRI},
        "SE.LPV.PRIM": {"2024-05-30": ""},
    }
