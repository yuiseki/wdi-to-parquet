"""Build all 4 profile×granularity combinations and print a size comparison table.

Usage:
    uv run python scripts/compare_profiles.py

Output dir: ~/.cache/wdi-to-parquet/profiles/
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wdi_to_parquet.cache import CacheStore
from wdi_to_parquet.fetch import fetch_indicator_zip
from wdi_to_parquet.profiles import (
    indicators_for_profile,
    years_for_granularity,
)
from wdi_to_parquet.transform import process_zip

CACHE = CacheStore(Path.home() / ".cache" / "wdi-to-parquet", max_age_days=30)
OUT_DIR = Path.home() / ".cache" / "wdi-to-parquet" / "profiles"
OUT_DIR.mkdir(parents=True, exist_ok=True)

COMBINATIONS = [
    ("minimum", "quinquennial"),
    ("minimum", "annual"),
    ("basic",   "quinquennial"),
    ("basic",   "annual"),
]


def build(profile: str, granularity: str) -> dict:
    indicators = indicators_for_profile(profile)
    years = years_for_granularity(granularity)
    out = OUT_DIR / f"wdi_{profile}_{granularity}.parquet"

    t0 = time.time()
    frames: list[pd.DataFrame] = []
    for indicator in indicators:
        zip_bytes = fetch_indicator_zip(indicator, CACHE)
        df = process_zip(zip_bytes, indicator=indicator, years=years)
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    combined.to_parquet(out, index=False, compression="zstd")
    elapsed = time.time() - t0

    return {
        "profile":      profile,
        "granularity":  granularity,
        "indicators":   len(indicators),
        "years":        len(years),
        "rows":         len(combined),
        "countries":    combined["iso3"].nunique(),
        "size_kb":      round(out.stat().st_size / 1024, 1),
        "elapsed_s":    round(elapsed, 1),
        "path":         str(out),
    }


def main() -> None:
    print("Building all profile×granularity combinations...\n")
    results = []
    for profile, granularity in COMBINATIONS:
        print(f"  {profile} × {granularity} ...", end=" ", flush=True)
        r = build(profile, granularity)
        results.append(r)
        print(f"{r['size_kb']} KB  ({r['elapsed_s']}s)")

    print("\n" + "=" * 72)
    print(f"{'Profile':<12} {'Granularity':<14} {'Inds':>5} {'Years':>6} "
          f"{'Rows':>8} {'Size KB':>8} {'Time s':>7}")
    print("-" * 72)
    baseline = results[0]["size_kb"]
    for r in results:
        ratio = f"×{r['size_kb']/baseline:.1f}" if r["size_kb"] != baseline else "base"
        print(f"{r['profile']:<12} {r['granularity']:<14} {r['indicators']:>5} "
              f"{r['years']:>6} {r['rows']:>8,} {r['size_kb']:>7.1f} "
              f"{r['elapsed_s']:>6.1f}  {ratio}")
    print("=" * 72)
    print(f"\nFiles written to: {OUT_DIR}")


if __name__ == "__main__":
    main()
