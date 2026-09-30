"""Audit-targeting simulations, after Ash et al. (2025), Section IV and Table 4.

Each year the agency audits `n_audits` municipalities. Three policies:

- random: the status quo lottery;
- targeted: the n highest predicted risks;
- fair: statistical parity across groups (the paper uses mayors' parties). The
  audits are split across groups in proportion to group size (largest
  remainder), then filled by risk within each group. This is the paper's
  post-processing approach: the prediction step is untouched.

Two evaluation modes, as in the paper:

- "sim": the outcome is the predicted probability itself, i.e. the predictions
  are treated as true corruption rates (Table 4, columns 1A and 2A). This is
  only meaningful if the model is calibrated, which is why models.py refuses
  resampling;
- "observed": the outcome is a real label, available only where one exists
  (columns 1B and 2B).

Reported per policy: the corruption rate among audited units, and the audit
rate among corrupt units, the paper's deterrence measure. Both are pooled over
years (total detections over total audits, total detections over total
corrupt).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PolicyResult:
    corruption_rate_if_audited: float
    audit_rate_if_corrupt: float
    audits: int


def _fair_quota(sizes: pd.Series, n: int) -> pd.Series:
    raw = sizes / sizes.sum() * n
    quota = np.floor(raw).astype(int)
    remainder = (raw - quota).sort_values(ascending=False)
    for g in remainder.index[: n - int(quota.sum())]:
        quota[g] += 1
    return np.minimum(quota, sizes)


def select(
    frame: pd.DataFrame,
    n_audits: int,
    *,
    policy: str,
    risk_col: str = "risk",
    year_col: str = "year",
    group_col: str | None = None,
    seed: int = 0,
) -> pd.Series:
    """Boolean mask of audited rows, `n_audits` per year."""
    rng = np.random.default_rng(seed)
    chosen = pd.Series(False, index=frame.index)
    for _, year in frame.groupby(year_col):
        n = min(n_audits, len(year))
        if policy == "random":
            idx = rng.choice(year.index.to_numpy(), size=n, replace=False)
        elif policy == "targeted":
            idx = year[risk_col].sort_values(ascending=False, kind="stable").index[:n]
        elif policy == "fair":
            if group_col is None:
                raise ValueError("fair targeting needs group_col")
            quota = _fair_quota(year.groupby(group_col).size(), n)
            idx = []
            for g, rows in year.groupby(group_col):
                top = rows[risk_col].sort_values(ascending=False, kind="stable")
                idx.extend(top.index[: quota[g]])
        else:
            raise ValueError(f"unknown policy {policy!r}")
        chosen.loc[idx] = True
    return chosen


def evaluate(frame: pd.DataFrame, audited: pd.Series, outcome_col: str) -> PolicyResult:
    """Pooled detection metrics; `outcome_col` holds labels or probabilities."""
    outcome = frame[outcome_col].astype(float)
    detected = outcome[audited].sum()
    return PolicyResult(
        corruption_rate_if_audited=float(detected / max(1, audited.sum())),
        audit_rate_if_corrupt=float(detected / outcome.sum())
        if outcome.sum() > 0
        else float("nan"),
        audits=int(audited.sum()),
    )


def expected_random(
    frame: pd.DataFrame, n_audits: int, outcome_col: str, year_col: str = "year"
) -> PolicyResult:
    """Closed-form expectation of the lottery, so the baseline carries no draw noise."""
    detected = audits = 0.0
    for _, year in frame.groupby(year_col):
        n = min(n_audits, len(year))
        detected += n * year[outcome_col].mean()
        audits += n
    total = frame[outcome_col].sum()
    return PolicyResult(
        corruption_rate_if_audited=float(detected / audits),
        audit_rate_if_corrupt=float(detected / total) if total > 0 else float("nan"),
        audits=int(audits),
    )


def audits_to_match(
    frame: pd.DataFrame, target_detections: float, *, risk_col: str, outcome_col: str
) -> int:
    """Fewest top-risk audits (pooled ranking) whose detections reach the target.

    The paper's "79 targeted audits instead of 150 random ones" statistic.
    """
    ordered = frame.sort_values(risk_col, ascending=False, kind="stable")[outcome_col].astype(float)
    reached = np.flatnonzero(ordered.cumsum().to_numpy() >= target_detections)
    if len(reached) == 0:
        raise ValueError("target exceeds total detections")
    return int(reached[0] + 1)
