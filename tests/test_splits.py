import numpy as np
import pytest

from itcorr.simulate import selective_panel
from itcorr.splits import outer_splits


@pytest.fixture(scope="module")
def panel():
    return selective_panel(n_municipalities=60, years=range(2010, 2016), seed=1)


def test_row_splits_partition_rows(panel):
    splits = outer_splits(panel, "row", n_splits=5)
    test = np.sort(np.concatenate([te for _, te in splits]))
    assert np.array_equal(test, np.arange(len(panel)))


def test_group_splits_never_share_a_municipality(panel):
    for tr, te in outer_splits(panel, "group", n_splits=5, seed=3):
        assert not set(panel.istat_code.iloc[tr]) & set(panel.istat_code.iloc[te])


def test_temporal_splits_train_on_the_past_with_a_gap(panel):
    for tr, te in outer_splits(panel, "temporal", test_years=[2014, 2015], gap=1):
        assert panel.year.iloc[tr].max() < panel.year.iloc[te].min() - 1


def test_unknown_strategy(panel):
    with pytest.raises(ValueError):
        outer_splits(panel, "random")
