"""CLI entry point for wdi-to-parquet."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

from wdi_to_parquet.cache import CacheStore
from wdi_to_parquet.fetch import fetch_indicator_zip
from wdi_to_parquet.transform import process_zip

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("wdi-to-parquet")

DEFAULT_INDICATORS = [
    "SP.POP.TOTL",      # Population, total
    "SP.POP.GROW",      # Population growth (annual %)
    "NY.GDP.MKTP.CD",   # GDP (current US$)
    "NY.GDP.PCAP.CD",   # GDP per capita (current US$)
    "AG.SRF.TOTL.K2",   # Surface area (sq. km)
    "SP.URB.TOTL.IN.ZS", # Urban population (% of total)
]

DEFAULT_YEARS = [1990, 1995, 2000, 2005, 2010, 2015, 2020, 2023, 2024]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert World Bank WDI indicators to long-format Parquet."
    )
    parser.add_argument(
        "--indicators", nargs="+", default=DEFAULT_INDICATORS,
        metavar="CODE",
        help="WDI indicator codes (default: 6 core indicators)",
    )
    parser.add_argument(
        "--years", nargs="+", type=int, default=DEFAULT_YEARS,
        metavar="YEAR",
        help="Years to include (default: 1990-2023 quinquennial)",
    )
    parser.add_argument(
        "--output", "-o", default="wdi_indicators.parquet",
        help="Output parquet file path (default: wdi_indicators.parquet)",
    )
    parser.add_argument(
        "--cache-dir", default=str(Path.home() / ".cache" / "wdi-to-parquet"),
        help="Directory for cached WDI zip files",
    )
    parser.add_argument(
        "--max-age-days", type=int, default=30,
        help="Cache TTL in days (default: 30)",
    )
    parser.add_argument(
        "--force-refresh", action="store_true",
        help="Ignore cache and re-download all indicators",
    )
    args = parser.parse_args(argv)

    cache = CacheStore(Path(args.cache_dir), max_age_days=0 if args.force_refresh else args.max_age_days)

    frames: list[pd.DataFrame] = []
    for indicator in args.indicators:
        logger.info("Processing %s ...", indicator)
        try:
            zip_bytes = fetch_indicator_zip(indicator, cache)
            df = process_zip(zip_bytes, indicator=indicator, years=args.years)
            logger.info("  %s: %d rows", indicator, len(df))
            frames.append(df)
        except Exception as e:
            logger.error("  %s failed: %s", indicator, e)

    if not frames:
        logger.error("No data produced.")
        return 1

    combined = pd.concat(frames, ignore_index=True)
    logger.info(
        "Total: %d rows, %d countries, %d indicators, years=%s",
        len(combined),
        combined["iso3"].nunique(),
        combined["indicator"].nunique(),
        sorted(combined["year"].unique()),
    )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(out, index=False, compression="zstd")
    logger.info("Written: %s (%d bytes)", out, out.stat().st_size)
    return 0


if __name__ == "__main__":
    sys.exit(main())
