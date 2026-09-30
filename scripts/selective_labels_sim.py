"""Monte Carlo: what does a model trained on *detected* corruption learn?

SIMULATED DATA ONLY. Nothing printed here is a finding about Italy; it is a
design check, run before any real data is touched (docs/RESEARCH_DESIGN.md,
section 4).

Two scenarios, same true corruption process, different detection:

- uniform: every region detects corrupt conduct with probability 0.5, so the
  observed label is a random thinning of the truth (the Brazilian situation,
  where the lottery makes detection independent of the municipality);
- selective: detection differs by region (0.9, 0.5, 0.2, 0.05) and the budget
  carries a regional signature, so a model can learn *where prosecutors are
  active* rather than *who is corrupt*.

For each, a boosted model is trained on observed labels with municipality-level
cross-validation, and its out-of-fold scores are compared with the observed
labels (what a researcher can measure) and with true corruption (what the
policy is for). A region-only logit is the "where is it" benchmark. Five seeds,
mean and standard deviation.

The grid is two cells, not the paper's 288, to keep the run to a few minutes;
the question here is about labels, not tuning.

Usage: python scripts/selective_labels_sim.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from itcorr.models import nested_cv
from itcorr.policy import evaluate, expected_random, select
from itcorr.simulate import feature_columns, selective_panel
from itcorr.splits import outer_splits

GRID = {
    "reg_alpha": [0.1],
    "reg_lambda": [1],
    "max_depth": [3, 5],
    "learning_rate": [0.1],
    "min_child_weight": [1],
}
SCENARIOS = {
    "uniform": dict(detection=(0.5, 0.5, 0.5, 0.5)),
    "selective": dict(detection=(0.9, 0.5, 0.2, 0.05)),
}
SEEDS = range(5)
AUDITS_PER_YEAR = 20


def region_only_oof(panel: pd.DataFrame, splits) -> np.ndarray:
    dummies = pd.get_dummies(panel.region, prefix="r").to_numpy(dtype=float)
    oof = np.full(len(panel), np.nan)
    for tr, te in splits:
        model = LogisticRegression(max_iter=1000).fit(dummies[tr], panel.label.iloc[tr])
        oof[te] = model.predict_proba(dummies[te])[:, 1]
    return oof


def run(scenario: str, seed: int) -> dict[str, float]:
    panel = selective_panel(
        n_municipalities=300,
        years=range(2010, 2018),
        region_signature=1.5,
        seed=seed,
        **SCENARIOS[scenario],
    )
    splits = outer_splits(panel, "group", n_splits=5, seed=seed)
    res = nested_cv(
        panel[feature_columns(panel)].to_numpy(),
        panel.label.to_numpy(),
        splits,
        grid=GRID,
        groups=panel.istat_code.to_numpy(),
        inner_splits=3,
        seed=seed,
    )
    scored = panel.assign(risk=res.oof)
    targeted = evaluate(scored, select(scored, AUDITS_PER_YEAR, policy="targeted"), "corrupt")
    lottery = expected_random(scored, AUDITS_PER_YEAR, "corrupt")
    return {
        "auc_vs_detected": roc_auc_score(panel.label, res.oof),
        "auc_vs_true": roc_auc_score(panel.corrupt, res.oof),
        "region_only_auc_vs_detected": roc_auc_score(panel.label, region_only_oof(panel, splits)),
        "true_detection_gain": targeted.corruption_rate_if_audited
        / lottery.corruption_rate_if_audited,
    }


def main() -> None:
    rows = [{"scenario": s, "seed": seed, **run(s, seed)} for s in SCENARIOS for seed in SEEDS]
    table = pd.DataFrame(rows).drop(columns="seed").groupby("scenario").agg(["mean", "std"])
    pd.set_option("display.width", 160)
    print("SIMULATED DATA - design check, not a result about Italy")
    print(table.round(3).T.to_string())


if __name__ == "__main__":
    main()
