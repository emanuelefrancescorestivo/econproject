"""Outer train/test splits.

Ash et al. (2025) split the rows (municipality-years) at random, and report a
split by municipality as a robustness check (their Supplemental Appendix
Table B4). With a panel, a row split lets the model see other years of the same
municipality at training time, so part of what it "predicts" is the
municipality's identity. Cerqua et al. (Oxford Bulletin of Economics and
Statistics) document this failure mode for panel data in general.

All three strategies are kept, so the gap between them can be reported rather
than hidden:

- "row": the paper's split, for a like-for-like comparison with its Table 2;
- "group": no municipality appears in both train and test;
- "temporal": train on earlier years, test on a later one, which is how a
  risk score would actually be used (score this year's budgets with a model fit
  on the past). `gap` drops the years just before the test year, because a
  corruption label is only observed after a detection lag.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, KFold

Split = tuple[np.ndarray, np.ndarray]


def outer_splits(
    frame: pd.DataFrame,
    strategy: str,
    *,
    n_splits: int = 5,
    seed: int = 0,
    group_col: str = "istat_code",
    year_col: str = "year",
    test_years: Sequence[int] | None = None,
    gap: int = 0,
) -> list[Split]:
    """Positional (train, test) index pairs for `frame`."""
    n = len(frame)
    if strategy == "row":
        kf = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
        return [(tr, te) for tr, te in kf.split(np.zeros(n))]
    if strategy == "group":
        groups = frame[group_col].to_numpy()
        # GroupKFold is deterministic; shuffle group identities for a seeded split.
        rng = np.random.default_rng(seed)
        uniq = np.unique(groups)
        relabel = dict(zip(uniq, rng.permutation(len(uniq)), strict=True))
        shuffled = np.array([relabel[g] for g in groups])
        gkf = GroupKFold(n_splits=n_splits)
        return [(tr, te) for tr, te in gkf.split(np.zeros(n), groups=shuffled)]
    if strategy == "temporal":
        if not test_years:
            raise ValueError("temporal splits need test_years")
        years = frame[year_col].to_numpy()
        out = []
        for ty in test_years:
            tr = np.flatnonzero(years < ty - gap)
            te = np.flatnonzero(years == ty)
            if len(tr) == 0 or len(te) == 0:
                raise ValueError(f"empty train or test set for test year {ty}")
            out.append((tr, te))
        return out
    raise ValueError(f"unknown strategy {strategy!r}; expected row, group or temporal")
