"""CLI entry point for wdi-to-parquet."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

from wdi_to_parquet.cache import CacheStore
from wdi_to_parquet.fetch import fetch_indicator_zip
from wdi_to_parquet.profiles import (
    INDICATORS_MINIMUM,
    YEARS_QUINQUENNIAL,
    indicators_for_profile,
    years_for_granularity,
)
from wdi_to_parquet.transform import process_zip

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("wdi-to-parquet")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert World Bank WDI indicators to long-format Parquet.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
profiles:
  minimum   6 core indicators (population, GDP, area, urban)  [default]
  basic     16 indicators adding health, social, environment

granularities:
  quinquennial  5-year steps 1990-2024  [default]
  annual        every year 1990-2024

--indicators and --years override --profile / --granularity when both given.
""",
    )
    parser.add_argument(
        "--profile", choices=["minimum", "basic"], default=None,
        help="Predefined indicator set (overridden by --indicators)",
    )
    parser.add_argument(
        "--granularity", choices=["quinquennial", "annual"], default=None,
        help="Year step size (overridden by --years)",
    )
    parser.add_argument(
        "--indicators", nargs="+", default=None,
        metavar="CODE",
        help="Explicit WDI indicator codes (overrides --profile)",
    )
    parser.add_argument(
        "--years", nargs="+", type=int, default=None,
        metavar="YEAR",
        help="Explicit years (overrides --granularity)",
    )
    parser.add_argument(
        "--output", "-o", default="wdi_indicators.parquet",
        help="Output Parquet file path (default: wdi_indicators.parquet)",
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

    # Resolve indicators: explicit list > profile > default (minimum)
    if args.indicators:
        indicators = args.indicators
    elif args.profile:
        indicators = indicators_for_profile(args.profile)
    else:
        indicators = INDICATORS_MINIMUM

    # Resolve years: explicit list > granularity > default (quinquennial)
    if args.years:
        years = args.years
    elif args.granularity:
        years = years_for_granularity(args.granularity)
    else:
        years = YEARS_QUINQUENNIAL

    cache = CacheStore(
        Path(args.cache_dir),
        max_age_days=0 if args.force_refresh else args.max_age_days,
    )

    frames: list[pd.DataFrame] = []
    for indicator in indicators:
        logger.info("Processing %s ...", indicator)
        try:
            zip_bytes = fetch_indicator_zip(indicator, cache)
            df = process_zip(zip_bytes, indicator=indicator, years=years)
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
