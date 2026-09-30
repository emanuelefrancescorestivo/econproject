import numpy as np
import pandas as pd
import pytest

from itcorr.metrics import precision_at_k, recall_at_k
from itcorr.policy import audits_to_match, evaluate, expected_random, select


@pytest.fixture
def frame():
    rng = np.random.default_rng(0)
    n = 200
    risk = rng.random(n)
    return pd.DataFrame(
        {
            "year": np.repeat([2020, 2021], n // 2),
            "party": rng.choice(["A", "B", "C"], size=n, p=[0.6, 0.3, 0.1]),
            "risk": risk,
            "corrupt": (rng.random(n) < risk).astype(int),
        }
    )


def test_targeting_a_perfect_score_detects_only_corrupt(frame):
    frame = frame.assign(risk=frame.corrupt + 0.0)
    res = evaluate(frame, select(frame, 10, policy="targeted"), "corrupt")
    assert res.corruption_rate_if_audited == 1.0 and res.audits == 20


def test_expected_random_matches_base_rate(frame):
    res = expected_random(frame, 10, "corrupt")
    assert res.corruption_rate_if_audited == pytest.approx(frame.corrupt.mean())
    assert res.audit_rate_if_corrupt == pytest.approx(20 / 200)


def test_fair_targeting_equalises_audit_rates(frame):
    audited = select(frame, 20, policy="fair", group_col="party")
    for _, year in frame.assign(audited=audited).groupby("year"):
        sizes = year.groupby("party").size()
        quota = year.groupby("party").audited.sum()
        # Statistical parity up to rounding: each group within one audit of its share.
        assert ((quota - sizes / sizes.sum() * 20).abs() < 1).all()
    assert audited.groupby(frame.year).sum().tolist() == [20, 20]


def test_targeting_beats_random_on_informative_risk(frame):
    targeted = evaluate(frame, select(frame, 10, policy="targeted"), "corrupt")
    random = expected_random(frame, 10, "corrupt")
    assert targeted.corruption_rate_if_audited > random.corruption_rate_if_audited


def test_audits_to_match():
    frame = pd.DataFrame({"risk": [0.9, 0.8, 0.1, 0.05], "y": [1, 1, 0, 1]})
    assert audits_to_match(frame, 2, risk_col="risk", outcome_col="y") == 2
    assert audits_to_match(frame, 3, risk_col="risk", outcome_col="y") == 4
    with pytest.raises(ValueError):
        audits_to_match(frame, 4, risk_col="risk", outcome_col="y")


def test_precision_and_recall_at_k():
    y, p = np.array([1, 0, 1, 0]), np.array([0.9, 0.8, 0.7, 0.1])
    assert precision_at_k(y, p, 2) == 0.5
    assert recall_at_k(y, p, 3) == 1.0
