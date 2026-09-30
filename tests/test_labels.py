import math

import pytest

from itcorr.labels import CorruptionEvent, build_panel_labels


def _label(frame, code, year):
    return frame.set_index(["istat_code", "year"]).loc[(code, year), "label"]


def test_conduct_years_are_positive_and_the_rest_unlabelled():
    ev = CorruptionEvent("058091", 2015, 2017, ("319",), "indictment")
    out = build_panel_labels([ev], ["058091", "015146"], range(2014, 2019))
    assert [_label(out, "058091", y) for y in (2015, 2016, 2017)] == [1.0, 1.0, 1.0]
    assert math.isnan(_label(out, "058091", 2014))
    assert math.isnan(_label(out, "015146", 2016))


def test_negatives_only_when_asked():
    ev = CorruptionEvent("058091", 2015, 2015, ("319",), "investigation")
    clean = build_panel_labels(
        [ev], ["058091", "015146"], [2015], screened_clean=[("015146", 2015)]
    )
    assert _label(clean, "015146", 2015) == 0.0
    pu = build_panel_labels([ev], ["058091", "015146"], [2015, 2016], unlabelled_as_negative=True)
    assert _label(pu, "058091", 2016) == 0.0 and _label(pu, "058091", 2015) == 1.0


def test_positive_beats_screened_clean():
    ev = CorruptionEvent("058091", 2015, 2015, ("353",), "conviction")
    out = build_panel_labels([ev], ["058091"], [2015], screened_clean=[("058091", 2015)])
    assert _label(out, "058091", 2015) == 1.0


@pytest.mark.parametrize(
    "event",
    [
        CorruptionEvent("058091", 2015, 2015, ("323",), "conviction"),  # abuso d'ufficio: broad
        CorruptionEvent("058091", 2015, 2015, ("319",), "investigation"),  # below min_stage
        CorruptionEvent("058091", 2015, 2015, ("319",), "conviction", acquitted=True),
    ],
)
def test_events_that_do_not_qualify(event):
    out = build_panel_labels([event], ["058091"], [2015], min_stage="indictment")
    assert math.isnan(_label(out, "058091", 2015))


def test_event_validation():
    with pytest.raises(ValueError):
        CorruptionEvent("58091", 2015, 2015, ("319",), "indictment")
    with pytest.raises(ValueError):
        CorruptionEvent("058091", 2016, 2015, ("319",), "indictment")
    with pytest.raises(ValueError):
        CorruptionEvent("058091", 2015, 2015, ("319",), "arrest")
