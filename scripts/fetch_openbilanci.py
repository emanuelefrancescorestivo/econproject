"""Download harmonised municipal accounts from OpenBilanci, with the ISTAT crosswalk.

Writes (all under data/, which is git-ignored apart from .gitkeep):

- data/raw/istat/Elenco-comuni-italiani.csv            ISTAT's current list
- data/raw/openbilanci/...                             one cached JSON per request
- data/interim/openbilanci_crosswalk.csv               slug -> ISTAT code, with match rule
- data/interim/openbilanci_<type>_long.csv.gz          one row per item, municipality, year

Requests are paced (--delay seconds, default 2) and cached, so an interrupted
run resumes where it stopped. The full harmonised panel is about 110,000
requests (some 60 hours at the default pace): start with --sample.

Examples (PowerShell: replace python with .venv\\Scripts\\python):

    python scripts/fetch_openbilanci.py --sample 20 --years 2019
    python scripts/fetch_openbilanci.py --all --years 2016 2017 2018 2019 2020 2021 2022
"""

from __future__ import annotations

import argparse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

from itcorr.sources.istat import ISTAT_LIST_URL, crosswalk, load_municipalities
from itcorr.sources.openbilanci import (
    HARMONISED_YEARS,
    USER_AGENT,
    Fetcher,
    fetch_accounts,
    territories,
    territories_url,
)

ROOT = Path(__file__).resolve().parents[1]


def istat_list(raw_dir: Path) -> Path:
    path = raw_dir / "istat" / "Elenco-comuni-italiani.csv"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(ISTAT_LIST_URL, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=120) as response:
            path.write_bytes(response.read())
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    who = parser.add_mutually_exclusive_group(required=True)
    who.add_argument("--sample", type=int, help="random sample of matched municipalities")
    who.add_argument("--all", action="store_true", help="every matched municipality")
    parser.add_argument("--years", type=int, nargs="+", default=list(HARMONISED_YEARS))
    parser.add_argument("--type", default="consuntivo", choices=["consuntivo", "preventivo"])
    parser.add_argument("--delay", type=float, default=2.0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    args = parser.parse_args()

    raw, interim = args.data_dir / "raw", args.data_dir / "interim"
    interim.mkdir(parents=True, exist_ok=True)
    fetcher = Fetcher(raw / "openbilanci", delay=args.delay)

    istat = load_municipalities(istat_list(raw))
    terr = crosswalk(territories(fetcher.get_json(territories_url())), istat)
    terr.to_csv(interim / "openbilanci_crosswalk.csv", index=False)
    print(f"ISTAT municipalities: {len(istat)}; OpenBilanci territories: {len(terr)}")
    print(terr["match"].fillna("unmatched").value_counts().to_string())

    matched = terr.dropna(subset=["istat_code"])
    if args.sample is not None:
        rng = np.random.default_rng(args.seed)
        pick = rng.choice(len(matched), size=min(args.sample, len(matched)), replace=False)
        matched = matched.iloc[np.sort(pick)]
    print(f"fetching {len(matched)} municipalities x {len(args.years)} years x 2 sections")

    long = fetch_accounts(fetcher, matched["slug"], args.years, args.type)
    long = long.merge(matched[["slug", "istat_code"]], on="slug", how="left")
    out = interim / f"openbilanci_{args.type}_long.csv.gz"
    long.to_csv(out, index=False)

    ok = long.dropna(subset=["item"]) if "item" in long else pd.DataFrame()
    failed = long[long["error"].notna()] if "error" in long else pd.DataFrame()
    print(f"wrote {out} ({len(ok)} item rows)")
    print(f"failed requests: {len(failed)}")
    if len(ok):
        per = ok.groupby(["slug", "year", "section"]).size().unstack("section")
        print("items per municipality-year:")
        print(per.describe().round(1).to_string())


if __name__ == "__main__":
    main()
