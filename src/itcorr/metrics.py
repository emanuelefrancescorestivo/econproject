"""Out-of-sample metrics.

The paper's Table 2 reports accuracy, AUC-ROC and F1 at a 0.5 threshold, which
suits its 42/58 class split. With rare Italian labels, accuracy rewards
predicting "clean" everywhere, so this module adds what an audit agency
actually needs: precision and recall among the top k (the audits it can
afford), average precision (area under the precision-recall curve), the Brier
score, and a binned calibration table (the paper's Figure 1).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    f1_score,
    roc_auc_score,
)


def _clean(y: np.ndarray, p: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    y, p = np.asarray(y, dtype=float), np.asarray(p, dtype=float)
    keep = ~(np.isnan(y) | np.isnan(p))
    return y[keep].astype(int), p[keep]


def precision_at_k(y: np.ndarray, p: np.ndarray, k: int) -> float:
    y, p = _clean(y, p)
    top = np.argsort(-p, kind="stable")[:k]
    return float(y[top].mean())


def recall_at_k(y: np.ndarray, p: np.ndarray, k: int) -> float:
    y, p = _clean(y, p)
    top = np.argsort(-p, kind="stable")[:k]
    return float(y[top].sum() / max(1, y.sum()))


def classification_report(
    y: np.ndarray, p: np.ndarray, *, threshold: float = 0.5, k: int | None = None
) -> dict[str, float]:
    y, p = _clean(y, p)
    single_class = len(np.unique(y)) < 2
    constant = np.ptp(p) == 0
    out = {
        "n": float(len(y)),
        "base_rate": float(y.mean()),
        "accuracy": float(accuracy_score(y, p >= threshold)),
        "f1": float(f1_score(y, p >= threshold, zero_division=0)),
        "auc_roc": float("nan") if single_class or constant else float(roc_auc_score(y, p)),
        "avg_precision": float("nan") if single_class else float(average_precision_score(y, p)),
        "brier": float(brier_score_loss(y, np.clip(p, 0, 1))),
    }
    if k is not None:
        out[f"precision_at_{k}"] = precision_at_k(y, p, k)
        out[f"recall_at_{k}"] = recall_at_k(y, p, k)
    return out


def calibration_table(y: np.ndarray, p: np.ndarray, n_bins: int = 20) -> pd.DataFrame:
    """Observed rate against mean prediction in equal-width bins (paper, Figure 1)."""
    y, p = _clean(y, p)
    edges = np.linspace(0, 1, n_bins + 1)
    bins = np.clip(np.digitize(p, edges[1:-1]), 0, n_bins - 1)
    frame = pd.DataFrame({"bin": bins, "y": y, "p": p})
    table = frame.groupby("bin").agg(
        n=("y", "size"), mean_pred=("p", "mean"), observed=("y", "mean")
    )
    return table.reset_index()
