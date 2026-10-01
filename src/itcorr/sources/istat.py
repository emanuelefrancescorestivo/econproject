"""ISTAT municipality list and the crosswalk from other sources' names to ISTAT codes.

Verified 2026-10-01: the current list is served at ISTAT_LIST_URL as a
semicolon-separated, Latin-1 file with one row per municipality in existence
(7,896 rows that day). It does not contain municipalities abolished by mergers.

Other sources identify a municipality by name and province abbreviation (and,
for the Ministry of the Interior, by its own "finloc" code, which is not the
ISTAT code). The crosswalk matches, in order:

1. Italian name and province abbreviation;
2. the first part of a bilingual name ("Selva dei Molini - Muehlwald") and
   province abbreviation;
3. the Italian name alone, when it is unique in Italy *and* the source gives
   the same region (catches the Sardinian province reforms, where the
   abbreviation changed but the name did not). Without the region check this
   rule mapped Calliano (AT), renamed since, onto Calliano (TN). Rows without
   a region code are not eligible for this rule.

The Ministry of the Interior's finloc code carries the ISTAT region code in
its second and third digits ("1070340250": region 07, Liguria). Checked on
2026-10-01 against the 7,387 OpenBilanci rows that match on name and province
and have a finloc code: 7 disagree, consistent with the few municipalities
that changed region; `finloc_region` is therefore a usable region source.

A source row that matches nothing is most often a municipality abolished by a
merger; it stays unmatched, with `match = None`, and is counted, never guessed.
An ISTAT code claimed by two source rows is marked "ambiguous" on both, and
neither keeps the code. Mapping abolished municipalities onto their successors
needs ISTAT's register of administrative changes (AUDIT item 9).
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd

ISTAT_LIST_URL = (
    "https://www.istat.it/storage/codici-unita-amministrative/Elenco-comuni-italiani.csv"
)

_COLUMNS = {
    "Codice Comune formato alfanumerico": "istat_code",
    "Codice Regione": "region_code",
    "Denominazione in italiano": "name_it",
    "Denominazione (Italiana e straniera)": "name_full",
    "Sigla automobilistica": "prov",
    "Denominazione Regione": "region",
    "Ripartizione geografica": "macro_area",
}


def normalise(name: str) -> str:
    """Lower-case ASCII letters and digits only: 'Sant'Agata de' Goti' -> 'santagatadegoti'."""
    ascii_ = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", ascii_.lower())


def _first_part(name: str) -> str:
    return re.split(r"\s+-\s+|/", str(name))[0]


def load_municipalities(path: str | Path) -> pd.DataFrame:
    """Read ISTAT's list into istat_code, name_it, name_full, prov, region, macro_area."""
    raw = pd.read_csv(path, sep=";", encoding="latin-1", dtype=str)
    raw.columns = [c.strip() for c in raw.columns]
    missing = set(_COLUMNS) - set(raw.columns)
    if missing:
        raise ValueError(f"ISTAT list lacks expected columns: {sorted(missing)}")
    out = raw[list(_COLUMNS)].rename(columns=_COLUMNS)
    out["istat_code"] = out["istat_code"].str.zfill(6)
    out["region_code"] = out["region_code"].str.zfill(2)
    return out


def finloc_region(code: str | None) -> str | None:
    """ISTAT region code from a finloc code such as 'GENOVA--1070340250' or '1070340250'."""
    if not isinstance(code, str) or not code:
        return None
    digits = code.split("--")[-1]
    return digits[1:3] if len(digits) >= 3 and digits.isdigit() else None


def crosswalk(source: pd.DataFrame, istat: pd.DataFrame) -> pd.DataFrame:
    """Add `istat_code` and `match` to a frame with `denominazione` and `prov` columns.

    An optional `region_code` column (two-digit ISTAT region) enables rule 3.
    """
    out = source.copy()
    key = out["denominazione"].map(lambda s: normalise(_first_part(s)))
    out["istat_code"] = None
    out["match"] = None

    rules = [
        ("name_prov", istat["name_it"].map(normalise)),
        ("first_part_prov", istat["name_full"].map(lambda s: normalise(_first_part(s)))),
    ]
    for rule, names in rules:
        lookup = dict(zip(names + "|" + istat["prov"], istat["istat_code"], strict=True))
        todo = out["istat_code"].isna()
        hits = (key + "|" + out["prov"])[todo].map(lookup)
        found = hits.notna()
        out.loc[hits[found].index, "istat_code"] = hits[found]
        out.loc[hits[found].index, "match"] = rule

    names = istat["name_it"].map(normalise)
    unique = names.map(names.value_counts()) == 1
    lookup = dict(zip(names[unique], istat["istat_code"][unique], strict=True))
    region_of = dict(zip(istat["istat_code"], istat["region_code"], strict=True))
    todo = out["istat_code"].isna()
    hits = key[todo].map(lookup)
    source_region = out.get("region_code", pd.Series(None, index=out.index))[todo]
    found = hits.notna() & (hits.map(region_of) == source_region)
    out.loc[hits[found].index, "istat_code"] = hits[found]
    out.loc[hits[found].index, "match"] = "name_unique"

    claimed = out["istat_code"].dropna()
    dup = claimed[claimed.duplicated(keep=False)].index
    out.loc[dup, "istat_code"] = None
    out.loc[dup, "match"] = "ambiguous"
    return out
