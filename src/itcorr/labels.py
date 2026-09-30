"""Corruption labels: from detected events to municipality-year targets.

Ash, Galletta and Giommoni (2025) label a municipality-year 1 when a random
federal audit found *narrow* corruption (illegal procurement, fraud,
favouritism, over-invoicing) in the budget years the auditors examined, and 0
when the audit found none. Years that were never audited carry no label.

Italy has no random corruption audits, so a label here is a *detected* event:
an investigation, indictment or conviction for a corruption offence involving a
municipality's administration, dated to the years of the alleged conduct (not
to the year the news broke). That is the closest analogue of "the budget years
the auditors examined". The event codebook is docs/CODEBOOK.md.

The absence of an event is not evidence of honesty. `build_panel_labels`
therefore distinguishes three states: 1 (conduct detected), 0 (only for
municipality-years the caller explicitly marks as screened and clean), and
missing (unlabelled). Treating every unlabelled year as 0 is the
positive-unlabelled assumption; it is available, but only by asking for it
(`unlabelled_as_negative=True`), because it is the assumption the research
design questions (docs/RESEARCH_DESIGN.md, section 4).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import pandas as pd

# Criminal-code articles counted as "narrow" corruption, the analogue of the
# Brollo et al. (2013) narrow measure used by Ash et al. Chosen: offences that
# require an exchange or a rigged award. Rejected: abuso d'ufficio (art. 323),
# which is closer to the "broad" mismanagement measure and was repealed in 2024
# (to be confirmed against the statute before the label is frozen). Also left
# out: 319-ter (corruption in judicial acts), which does not involve a
# municipality's administration.
NARROW_OFFENCES: frozenset[str] = frozenset(
    {
        "314",  # peculato
        "317",  # concussione
        "318",  # corruzione per l'esercizio della funzione
        "319",  # corruzione per un atto contrario ai doveri d'ufficio
        "319-quater",  # induzione indebita a dare o promettere utilita
        "320",  # corruzione di persona incaricata di un pubblico servizio
        "321",  # pene per il corruttore
        "322",  # istigazione alla corruzione
        "346-bis",  # traffico di influenze illecite
        "353",  # turbata liberta degli incanti
        "353-bis",  # turbata liberta del procedimento di scelta del contraente
    }
)

# Procedural stages, ordered by how much evidence they require.
STAGES: tuple[str, ...] = ("investigation", "indictment", "conviction")


@dataclass(frozen=True)
class CorruptionEvent:
    """One detected episode, as coded from a source document (docs/CODEBOOK.md)."""

    istat_code: str  # six-digit ISTAT municipality code, as a string
    conduct_start: int  # first year of the alleged conduct
    conduct_end: int  # last year of the alleged conduct
    offences: tuple[str, ...]  # criminal-code articles, e.g. ("319", "353")
    stage: str  # furthest stage reached: one of STAGES
    acquitted: bool = False  # all defendants acquitted or case dismissed
    source_id: str = ""

    def __post_init__(self) -> None:
        if self.stage not in STAGES:
            raise ValueError(f"unknown stage {self.stage!r}; expected one of {STAGES}")
        if self.conduct_end < self.conduct_start:
            raise ValueError("conduct_end precedes conduct_start")
        if len(self.istat_code) != 6 or not self.istat_code.isdigit():
            raise ValueError(f"ISTAT code must be six digits, got {self.istat_code!r}")

    def is_narrow(self) -> bool:
        return any(o in NARROW_OFFENCES for o in self.offences)


def build_panel_labels(
    events: Iterable[CorruptionEvent],
    municipalities: Iterable[str],
    years: Iterable[int],
    *,
    min_stage: str = "investigation",
    drop_acquitted: bool = True,
    screened_clean: Iterable[tuple[str, int]] = (),
    unlabelled_as_negative: bool = False,
) -> pd.DataFrame:
    """Return one row per municipality-year with a `label` column.

    label is 1.0 for a year covered by the conduct period of a qualifying
    event, 0.0 for a year in `screened_clean` (or for every other year when
    `unlabelled_as_negative`), and NaN otherwise. A qualifying event is narrow,
    reached at least `min_stage`, and (by default) did not end in acquittal.
    A positive always wins over a screened-clean mark for the same year.
    """
    if min_stage not in STAGES:
        raise ValueError(f"unknown stage {min_stage!r}")
    floor = STAGES.index(min_stage)
    muni = sorted(set(municipalities))
    yrs = sorted(set(years))
    index = pd.MultiIndex.from_product([muni, yrs], names=["istat_code", "year"])
    label = pd.Series(0.0 if unlabelled_as_negative else float("nan"), index=index)

    for key in screened_clean:
        if key in label.index:
            label.loc[key] = 0.0

    for ev in events:
        if not ev.is_narrow() or STAGES.index(ev.stage) < floor:
            continue
        if drop_acquitted and ev.acquitted:
            continue
        for year in range(ev.conduct_start, ev.conduct_end + 1):
            key = (ev.istat_code, year)
            if key in label.index:
                label.loc[key] = 1.0

    return label.rename("label").reset_index()
