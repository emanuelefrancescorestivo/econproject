"""Synthetic municipality panels with *selective* labels.

Nothing produced here is a result about Italy. The generator exists for two
purposes: tests, and the Monte Carlo in scripts/selective_labels_sim.py, which
asks the design question the Brazilian setting did not have to ask: how much
does a model trained on *detected* corruption learn about *detection* instead
of corruption?

Data-generating process (all parameters are arguments, with stated defaults):

- municipalities belong to regions; each region has a prosecution intensity
  q_r, the probability that corrupt conduct is detected in a given year;
- budget features x_it are Gaussian, with a region-specific shift of size
  `region_signature` in the first few features, so a model can recognise the
  region from the budget;
- true corruption c_it ~ Bernoulli(sigmoid(a + x_it' b + u_r)), with u_r a
  region effect on true corruption;
- the observed label is c_it * d_it with d_it ~ Bernoulli(q_r).

When q_r varies across regions and the budget reveals the region, a model can
score well against observed labels by learning q_r, not c.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-z))


def selective_panel(
    *,
    n_municipalities: int = 400,
    years: range = range(2010, 2020),
    n_features: int = 20,
    n_informative: int = 5,
    n_regions: int = 4,
    intercept: float = -2.0,
    signal: float = 0.8,
    region_corruption: tuple[float, ...] | None = None,
    detection: tuple[float, ...] | None = None,
    region_signature: float = 1.0,
    seed: int = 0,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    region_corruption = region_corruption or tuple(0.0 for _ in range(n_regions))
    detection = detection or tuple(0.5 for _ in range(n_regions))
    if len(region_corruption) != n_regions or len(detection) != n_regions:
        raise ValueError("region_corruption and detection need one entry per region")

    region = rng.integers(0, n_regions, size=n_municipalities)
    muni_effect = rng.normal(0, 0.5, size=(n_municipalities, n_features))
    beta = np.zeros(n_features)
    beta[:n_informative] = signal * rng.choice([-1.0, 1.0], size=n_informative)
    # Region signature lives in features the true model does not use.
    signature = rng.normal(0, region_signature, size=(n_regions, n_features))
    signature[:, :n_informative] = 0.0

    rows = []
    for t in years:
        x = muni_effect + signature[region] + rng.normal(0, 1, size=(n_municipalities, n_features))
        logit = intercept + x @ beta + np.asarray(region_corruption)[region]
        p_true = _sigmoid(logit)
        corrupt = rng.random(n_municipalities) < p_true
        detected = corrupt & (rng.random(n_municipalities) < np.asarray(detection)[region])
        frame = pd.DataFrame(x, columns=[f"x{j:02d}" for j in range(n_features)])
        frame.insert(0, "istat_code", [f"{i:06d}" for i in range(n_municipalities)])
        frame.insert(1, "year", t)
        frame.insert(2, "region", region)
        frame["p_true"] = p_true
        frame["corrupt"] = corrupt.astype(int)
        frame["label"] = detected.astype(int)
        rows.append(frame)
    return pd.concat(rows, ignore_index=True)


def feature_columns(frame: pd.DataFrame) -> list[str]:
    return [c for c in frame.columns if c.startswith("x")]
