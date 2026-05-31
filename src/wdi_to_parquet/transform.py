"""Parse and transform WDI CSV data into long-format DataFrames."""

from __future__ import annotations

import io
import zipfile

import pandas as pd


def parse_wdi_csv(raw: bytes) -> pd.DataFrame:
    """Parse the main API CSV from raw bytes, skipping the 4 WDI header rows."""
    return pd.read_csv(io.BytesIO(raw), skiprows=4, dtype=str, on_bad_lines="skip")


def parse_country_metadata(raw: bytes) -> set[str]:
    """Return ISO3 codes of real countries (those with a non-empty Region)."""
    meta = pd.read_csv(io.BytesIO(raw), dtype=str)
    real = meta[meta["Region"].notna() & (meta["Region"].str.strip() != "")]
    return set(real["Country Code"].dropna())


def filter_real_countries(df: pd.DataFrame, real_iso3: set[str]) -> pd.DataFrame:
    """Drop aggregate/regional rows, keeping only sovereign country rows."""
    return df[df["Country Code"].isin(real_iso3)].copy()


def melt_to_long(
    df: pd.DataFrame,
    indicator: str,
    years: list[int],
) -> pd.DataFrame:
    """Melt a wide WDI DataFrame into long format for the given years.

    Returns a DataFrame with columns: iso3, year, indicator, value.
    Rows with missing values are dropped.
    """
    year_cols = [str(y) for y in years if str(y) in df.columns]
    long = df.melt(
        id_vars=["Country Code"],
        value_vars=year_cols,
        var_name="year",
        value_name="value",
    )
    long = long.rename(columns={"Country Code": "iso3"})
    long["year"] = long["year"].astype(int)
    long["value"] = pd.to_numeric(long["value"], errors="coerce").astype("float64")
    long["indicator"] = indicator
    long = long.dropna(subset=["value"])
    return long[["iso3", "year", "indicator", "value"]].reset_index(drop=True)


def process_zip(
    zip_bytes: bytes,
    indicator: str,
    years: list[int],
) -> pd.DataFrame:
    """Full pipeline: zip bytes → long-format DataFrame for one indicator."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        data_name = next(n for n in names if n.startswith("API_"))
        meta_name = next(n for n in names if n.startswith("Metadata_Country"))
        raw_data = zf.read(data_name)
        raw_meta = zf.read(meta_name)

    df = parse_wdi_csv(raw_data)
    real = parse_country_metadata(raw_meta)
    filtered = filter_real_countries(df, real)
    return melt_to_long(filtered, indicator=indicator, years=years)
