"""Municipal budgets from OpenBilanci (openpolis), the paper's X for Italy.

What was verified on 2026-10-01, by requesting the endpoints below:

- `/search/territori?q=` returns every territory (8,227 municipalities,
  including ones since abolished) with name, province abbreviation, the
  Ministry of the Interior's "finloc" code and a slug. Its `q` filter and
  `page` parameter were ignored: every call returned the full list.
- `/armonizzati/bilanci/<slug>/<section>/dettaglio.json?year=Y&type=T`, with
  section `entrate` or `spese` and type `consuntivo` (year-end accounts) or
  `preventivo` (budget), returns a tree of items. Each node has `slug`,
  `label`, `values` ([{year: {"abs": euros, "pc": euros per inhabitant}}]) and
  optionally `children`. For Genova 2019 the year-end accounts had 31 revenue
  and 272 expenditure leaves (spending by mission > programme > title).
- These are the harmonised accounts (d.lgs. 118/2011), years 2016 to 2022.
  The 2005-2015 accounts are offered by the site under a different scheme,
  through a route that was not reachable from the development container
  (AUDIT item 8).
- Source of the figures: Ministry of the Interior, Finanza Locale. Licence:
  CC BY-NC-SA 4.0 (openbilanci.it/pages/licenze). Data is not committed.

One request per municipality, year, section and type: the full harmonised
panel is about 110,000 requests. The fetcher therefore caches every answer on
disk and waits between requests; ask openpolis for a bulk export, or use the
BDAP open-data catalogue, before scraping the whole country.
"""

from __future__ import annotations

import json
import time
import urllib.request
from collections.abc import Iterable
from pathlib import Path

import pandas as pd

from itcorr.sources.istat import finloc_region

BASE = "https://openbilanci.it"
SECTIONS = ("entrate", "spese")
TYPES = ("consuntivo", "preventivo")
HARMONISED_YEARS = range(2016, 2023)
USER_AGENT = "itcorr research (github.com/emanuelefrancescorestivo/econproject)"


def territories_url() -> str:
    return f"{BASE}/search/territori?q="


def detail_url(slug: str, section: str, year: int, kind: str = "consuntivo") -> str:
    if section not in SECTIONS:
        raise ValueError(f"section must be one of {SECTIONS}")
    if kind not in TYPES:
        raise ValueError(f"type must be one of {TYPES}")
    return f"{BASE}/armonizzati/bilanci/{slug}/{section}/dettaglio.json?year={year}&type={kind}"


class Fetcher:
    """GET with an on-disk cache and a fixed pause between network requests."""

    def __init__(self, cache_dir: str | Path, delay: float = 2.0, timeout: float = 60.0):
        self.cache_dir = Path(cache_dir)
        self.delay = delay
        self.timeout = timeout
        self._last = 0.0

    def _path(self, url: str) -> Path:
        name = url.removeprefix(BASE).strip("/").replace("/", "__").replace("?", "__")
        return self.cache_dir / (name.replace("&", "__").replace("=", "-") + ".json")

    def get_json(self, url: str):
        path = self._path(url)
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        wait = self.delay - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            body = response.read().decode("utf-8")
        self._last = time.monotonic()
        data = json.loads(body)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        return data


def territories(payload: dict) -> pd.DataFrame:
    """The `/search/territori` answer: slug, denominazione, prov, cod_finloc, region_code."""
    frame = pd.DataFrame(payload["items"])[["slug", "denominazione", "prov", "cod_finloc"]]
    return frame.assign(region_code=frame["cod_finloc"].map(finloc_region))


def flatten(tree: list[dict], section: str) -> pd.DataFrame:
    """One row per node and year: item, section, label path, leaf flag, euros, euros per head.

    Internal nodes (totals and subtotals) are kept and flagged, because the
    paper's 797 variables mix aggregates and detail; dropping them is a
    modelling choice made later, not here.
    """
    rows = []

    def walk(node: dict, path: tuple[str, ...]) -> None:
        here = (*path, node["label"])
        children = node.get("children") or []
        for entry in node.get("values", []):
            for year, value in entry.items():
                rows.append(
                    {
                        "item": node["slug"],
                        "section": section,
                        "label": " > ".join(here),
                        "is_leaf": not children,
                        "year": int(year),
                        "abs": value.get("abs"),
                        "pc": value.get("pc"),
                    }
                )
        for child in children:
            walk(child, here)

    for root in tree:
        walk(root, ())
    return pd.DataFrame(rows)


def fetch_accounts(
    fetcher: Fetcher,
    slugs: Iterable[str],
    years: Iterable[int] = HARMONISED_YEARS,
    kind: str = "consuntivo",
) -> pd.DataFrame:
    """Long frame of every item for the given municipalities and years.

    A request that fails (no accounts filed, server error) is recorded in the
    `error` column of a separate row rather than stopping the run, so missing
    accounts are counted instead of silently absent.
    """
    frames, failures = [], []
    for slug in slugs:
        for year in years:
            for section in SECTIONS:
                url = detail_url(slug, section, year, kind)
                try:
                    tree = fetcher.get_json(url)
                except Exception as exc:  # noqa: BLE001 - recorded, not swallowed
                    failures.append(
                        {"slug": slug, "year": year, "section": section, "error": repr(exc)}
                    )
                    continue
                if not tree:  # the server answers null when no accounts were filed
                    failures.append(
                        {"slug": slug, "year": year, "section": section, "error": "no data"}
                    )
                    continue
                flat = flatten(tree, section)
                flat.insert(0, "slug", slug)
                frames.append(flat)
    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if failures:
        out = pd.concat([out, pd.DataFrame(failures)], ignore_index=True)
    return out


def wide(long: pd.DataFrame, value: str = "pc", leaves_only: bool = False) -> pd.DataFrame:
    """One row per municipality-year, one column per item (`<section>:<item>`)."""
    frame = long.dropna(subset=["item"])
    if leaves_only:
        frame = frame[frame["is_leaf"]]
    frame = frame.assign(column=frame["section"] + ":" + frame["item"])
    return frame.pivot_table(
        index=["slug", "year"], columns="column", values=value, aggfunc="first"
    ).reset_index()
