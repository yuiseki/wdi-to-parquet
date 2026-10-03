#!/usr/bin/env python3
"""Push every release's Parquet, rebuilt CSVs and the card to the Hugging Face Hub.

Every release filed under data/raw/ must be declared in the card, one
subset per table, and must have passed through 03_export.py. The World
Bank's own zips are never uploaded (they hold the indicators left out);
only their MANIFEST.json goes up, as the record of what was converted.

    uv run python scripts/publish.py             # dry run
    uv run python scripts/publish.py --push
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
REPO = "yuiseki/worldbank-wdi"
TABLES = ("data", "countries", "series", "country_series", "footnotes", "series_time")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--push", action="store_true")
    a = ap.parse_args()

    card = (DATA / "README.md").read_text(encoding="utf-8")
    files = ["README.md", "LICENSE", "provenance.yaml"]
    versions = sorted(p.name for p in (DATA / "raw").iterdir() if (p / "MANIFEST.json").exists())
    union = None
    for v in versions:
        for t in TABLES:
            decl = f"- config_name: '{v}.{t}'\n  data_files: parquet/{v}/{t}.parquet\n"
            if decl not in card:
                raise SystemExit(f"the card does not declare the subset {v}.{t}")
            files.append(f"parquet/{v}/{t}.parquet")
        excl = json.loads((DATA / "parquet" / v / "excluded.json").read_text())
        if excl["releases_considered"] != versions:
            raise SystemExit(f"{v} was exported before the releases {versions}; run 03_export.py")
        if union is None:
            union = set(excl["indicators"])
        elif set(excl["indicators"]) != union:
            raise SystemExit(f"{v} leaves out other indicators than the other releases")
        files += [f"parquet/{v}/excluded.json", f"csv/{v}/WDI_CSV_redistributable.zip",
                  f"raw/{v}/MANIFEST.json"]
    total = sum((DATA / f).stat().st_size for f in files)
    print(f"{a.repo}\n  {len(versions)} releases, {len(files)} files, {total / 1e6:.1f} MB")
    if not a.push:
        print("\ndry run. pass --push to upload")
        return 0

    from huggingface_hub import HfApi

    api = HfApi()
    api.create_repo(a.repo, repo_type="dataset", exist_ok=True, private=False)
    api.upload_folder(folder_path=str(DATA), repo_id=a.repo, repo_type="dataset", allow_patterns=files)
    print(f"\npushed to https://huggingface.co/datasets/{a.repo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
