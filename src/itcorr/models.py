"""The prediction step of Ash, Galletta and Giommoni (2025), Section II.

What is reproduced, and where it departs from the paper:

- XGBoost with the paper's 288-cell grid (footnote 13: L1 and L2 penalties in
  {0.1, 0.5, 1, 2}, max depth in {5, 10, 20}, learning rate in {0.1, 0.5},
  minimum child weight in {1, 3, 5}) and early stopping with patience 10.
- Nested cross-validation: an inner 5-fold search on each outer training set.
  The paper does not state the inner selection metric; AUC-ROC is used here
  because the downstream use is a ranking (audit targeting). Early stopping
  and scoring share the inner validation fold, which is standard but slightly
  optimistic; the outer test fold is never touched.
- The refit on the full outer training set has no validation set left for
  early stopping, so it uses the mean best iteration from the inner folds.
- Missing values: the paper imputes the column mean. That is kept for
  fidelity, fitted on training rows only (a mean over train+test would leak).
- Class imbalance: the paper's classes were 42/58 and needed nothing. Italian
  labels will be rare. `scale_pos_weight` reweights the loss; resampling such
  as SMOTE is deliberately not offered, because it distorts predicted
  probabilities (van den Goorbergh et al., JAMIA 2022) and the policy
  simulation reads those probabilities as rates (policy.py).
- Baselines follow the paper's Table 2: modal guess, OLS, Lasso and an
  elastic-net logit. They are standardised here (the paper does not say);
  a baseline that is not given a fair chance makes the boosted model look
  better than it is.
"""

from __future__ import annotations

import itertools
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LassoCV, LinearRegression, LogisticRegressionCV
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold, StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from itcorr.splits import Split

PAPER_GRID: dict[str, list[float]] = {
    "reg_alpha": [0.1, 0.5, 1, 2],
    "reg_lambda": [0.1, 0.5, 1, 2],
    "max_depth": [5, 10, 20],
    "learning_rate": [0.1, 0.5],
    "min_child_weight": [1, 3, 5],
}
EARLY_STOPPING_ROUNDS = 10
MAX_TREES = 1000


def grid_cells(grid: Mapping[str, Sequence[float]]) -> list[dict[str, float]]:
    keys = list(grid)
    return [dict(zip(keys, values, strict=True)) for values in itertools.product(*grid.values())]


def _imputer() -> SimpleImputer:
    return SimpleImputer(strategy="mean", keep_empty_features=True)


def _xgb(params: Mapping[str, float], n_estimators: int, *, early: bool, spw: float, seed: int):
    return XGBClassifier(
        **params,
        n_estimators=n_estimators,
        early_stopping_rounds=EARLY_STOPPING_ROUNDS if early else None,
        eval_metric="logloss",
        tree_method="hist",
        scale_pos_weight=spw,
        random_state=seed,
        n_jobs=-1,
    )


def _inner_folds(y: np.ndarray, groups: np.ndarray | None, n_splits: int, seed: int) -> list[Split]:
    zeros = np.zeros(len(y))
    if groups is not None:
        rng = np.random.default_rng(seed)
        uniq = np.unique(groups)
        relabel = dict(zip(uniq, rng.permutation(len(uniq)), strict=True))
        shuffled = np.array([relabel[g] for g in groups])
        return list(GroupKFold(n_splits=n_splits).split(zeros, groups=shuffled))
    return list(StratifiedKFold(n_splits, shuffle=True, random_state=seed).split(zeros, y))


def select_params(
    X: np.ndarray,
    y: np.ndarray,
    *,
    grid: Mapping[str, Sequence[float]] = PAPER_GRID,
    groups: np.ndarray | None = None,
    inner_splits: int = 5,
    spw: float = 1.0,
    seed: int = 0,
) -> tuple[dict[str, float], int, float]:
    """Inner grid search. Returns (best cell, number of trees, mean inner AUC)."""
    folds = _inner_folds(y, groups, inner_splits, seed)
    best: tuple[dict[str, float], int, float] | None = None
    for cell in grid_cells(grid):
        scores, trees = [], []
        for tr, va in folds:
            if len(np.unique(y[va])) < 2 or len(np.unique(y[tr])) < 2:
                continue
            imp = _imputer().fit(X[tr])
            model = _xgb(cell, MAX_TREES, early=True, spw=spw, seed=seed)
            model.fit(
                imp.transform(X[tr]), y[tr], eval_set=[(imp.transform(X[va]), y[va])], verbose=False
            )
            p = model.predict_proba(imp.transform(X[va]))[:, 1]
            scores.append(roc_auc_score(y[va], p))
            trees.append(model.best_iteration + 1)
        if not scores:
            raise ValueError("no inner fold contains both classes; too few positives")
        score = float(np.mean(scores))
        if best is None or score > best[2]:
            best = (cell, max(1, round(float(np.mean(trees)))), score)
    assert best is not None
    return best


@dataclass
class FoldResult:
    params: dict[str, float]
    n_trees: int
    inner_auc: float
    test_idx: np.ndarray
    imputer: SimpleImputer = field(repr=False)
    model: XGBClassifier = field(repr=False)


@dataclass
class NestedCVResult:
    """Out-of-fold predictions plus one fitted model per outer fold."""

    oof: np.ndarray  # NaN where a row was never in a test fold
    folds: list[FoldResult]

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Average of the fold models, the paper's rule for unaudited units (footnote 21)."""
        X = np.asarray(X, dtype=float)
        preds = [f.model.predict_proba(f.imputer.transform(X))[:, 1] for f in self.folds]
        return np.mean(preds, axis=0)

    def feature_importance(self) -> np.ndarray:
        """Split counts ("weight") averaged over folds, the paper's importance measure.

        Split counts favour continuous, high-cardinality features; report SHAP
        values alongside before interpreting a ranking.
        """
        out = []
        for f in self.folds:
            booster = f.model.get_booster()
            n = booster.num_features()
            scores = booster.get_score(importance_type="weight")
            out.append([scores.get(f"f{i}", 0.0) for i in range(n)])
        return np.mean(out, axis=0)


def nested_cv(
    X: np.ndarray,
    y: np.ndarray,
    splits: Sequence[Split],
    *,
    grid: Mapping[str, Sequence[float]] = PAPER_GRID,
    groups: np.ndarray | None = None,
    inner_splits: int = 5,
    spw: float = 1.0,
    seed: int = 0,
) -> NestedCVResult:
    X = np.asarray(X, dtype=float)
    y = np.asarray(y)
    if np.isnan(y.astype(float)).any():
        raise ValueError("labels contain NaN; drop unlabelled rows or choose a PU assumption first")
    y = y.astype(int)
    oof = np.full(len(y), np.nan)
    folds = []
    for tr, te in splits:
        g = None if groups is None else np.asarray(groups)[tr]
        params, n_trees, inner = select_params(
            X[tr], y[tr], grid=grid, groups=g, inner_splits=inner_splits, spw=spw, seed=seed
        )
        imp = _imputer().fit(X[tr])
        model = _xgb(params, n_trees, early=False, spw=spw, seed=seed)
        model.fit(imp.transform(X[tr]), y[tr], verbose=False)
        oof[te] = model.predict_proba(imp.transform(X[te]))[:, 1]
        folds.append(FoldResult(params, n_trees, inner, te, imp, model))
    return NestedCVResult(oof, folds)


def baseline_oof(
    X: np.ndarray, y: np.ndarray, splits: Sequence[Split], seed: int = 0
) -> dict[str, np.ndarray]:
    """Out-of-fold scores of the paper's Table 2 baselines."""
    X = np.asarray(X, dtype=float)
    y = np.asarray(y).astype(int)
    out = {name: np.full(len(y), np.nan) for name in ("guessing", "ols", "lasso", "logit_enet")}
    for tr, te in splits:
        # Modal guess: a constant score, so AUC is undefined, as in the paper.
        out["guessing"][te] = float(y[tr].mean() >= 0.5)
        ols = make_pipeline(_imputer(), StandardScaler(), LinearRegression()).fit(X[tr], y[tr])
        out["ols"][te] = np.clip(ols.predict(X[te]), 0, 1)
        lasso = make_pipeline(_imputer(), StandardScaler(), LassoCV(cv=5, random_state=seed))
        out["lasso"][te] = np.clip(lasso.fit(X[tr], y[tr]).predict(X[te]), 0, 1)
        logit = make_pipeline(
            _imputer(),
            StandardScaler(),
            LogisticRegressionCV(
                Cs=10,
                solver="saga",
                l1_ratios=[0.1, 0.5, 0.9],  # elastic net (scikit-learn >= 1.8 API)
                use_legacy_attributes=False,
                scoring="roc_auc",
                max_iter=5000,
                random_state=seed,
            ),
        )
        out["logit_enet"][te] = logit.fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
    return out
