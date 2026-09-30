import numpy as np
import pytest

from itcorr.metrics import classification_report
from itcorr.models import PAPER_GRID, baseline_oof, grid_cells, nested_cv
from itcorr.simulate import feature_columns, selective_panel
from itcorr.splits import outer_splits

SMALL_GRID = {
    "reg_alpha": [0.1],
    "reg_lambda": [1],
    "max_depth": [2, 3],
    "learning_rate": [0.1],
    "min_child_weight": [1],
}


def test_paper_grid_has_288_cells():
    assert len(grid_cells(PAPER_GRID)) == 288


@pytest.fixture(scope="module")
def panel():
    # Detection is uniform here, so observed labels are a thinned copy of the truth.
    return selective_panel(
        n_municipalities=150,
        years=range(2010, 2016),
        intercept=-0.5,
        signal=1.0,
        detection=(1.0, 1.0, 1.0, 1.0),
        seed=2,
    )


def test_nested_cv_recovers_signal_out_of_sample(panel):
    X, y = panel[feature_columns(panel)].to_numpy(), panel.label.to_numpy()
    splits = outer_splits(panel, "group", n_splits=3, seed=0)
    res = nested_cv(
        X, y, splits, grid=SMALL_GRID, groups=panel.istat_code.to_numpy(), inner_splits=3
    )
    report = classification_report(y, res.oof)
    assert not np.isnan(res.oof).any()
    assert report["auc_roc"] > 0.75
    assert res.predict(X[:5]).shape == (5,)
    assert res.feature_importance().shape == (X.shape[1],)


def test_imputation_uses_training_rows_only(panel):
    X = panel[feature_columns(panel)].to_numpy().copy()
    y = panel.label.to_numpy()
    splits = outer_splits(panel, "row", n_splits=3)
    X[splits[0][1], 0] = np.nan  # column 0 missing in the first test fold only
    res = nested_cv(X, y, splits[:1], grid=SMALL_GRID, inner_splits=3)
    fitted_mean = res.folds[0].imputer.statistics_[0]
    assert fitted_mean == pytest.approx(np.nanmean(X[splits[0][0], 0]))


def test_nan_labels_are_refused(panel):
    y = panel.label.to_numpy().astype(float)
    y[0] = np.nan
    with pytest.raises(ValueError):
        nested_cv(
            panel[feature_columns(panel)].to_numpy(), y, outer_splits(panel, "row"), grid=SMALL_GRID
        )


def test_baselines_run_and_guessing_has_no_auc(panel):
    X, y = panel[feature_columns(panel)].to_numpy(), panel.label.to_numpy()
    oof = baseline_oof(X, y, outer_splits(panel, "row", n_splits=3))
    assert set(oof) == {"guessing", "ols", "lasso", "logit_enet"}
    assert np.isnan(classification_report(y, oof["guessing"])["auc_roc"])
    assert classification_report(y, oof["logit_enet"])["auc_roc"] > 0.75
