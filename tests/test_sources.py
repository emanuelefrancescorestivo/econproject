import json
from pathlib import Path

import pandas as pd
import pytest

from itcorr.sources.istat import crosswalk, finloc_region, load_municipalities, normalise
from itcorr.sources.openbilanci import Fetcher, detail_url, flatten, territories, wide

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def istat():
    return load_municipalities(FIXTURES / "istat_sample.csv")


def test_load_municipalities_reads_the_real_layout(istat):
    genova = istat.set_index("istat_code").loc["010025"]
    assert (genova.name_it, genova.prov, genova.region_code) == ("Genova", "GE", "07")


def test_normalise_and_finloc_region():
    assert normalise("Sant'Agata de' Goti") == "santagatadegoti"
    assert finloc_region("GENOVA--1070340250") == "07"
    assert finloc_region(None) is None


def test_crosswalk_rules(istat):
    source = pd.DataFrame(
        [
            ("Genova", "GE", "07"),  # name and province
            ("Selva dei Molini - Muehlwald", "BZ", "04"),  # bilingual name
            ("Arzachena", "OT", "20"),  # abolished province, unique name, same region
            ("Calliano", "AT", "01"),  # unique name but another region: must not match
            ("Castro", "XX", "03"),  # name shared by two municipalities: must not match
            ("Castro", "LE", "16"),
        ],
        columns=["denominazione", "prov", "region_code"],
    )
    out = crosswalk(source, istat)
    assert out.istat_code.tolist() == ["010025", "021088", "090006", None, None, "075096"]
    assert out.match.tolist() == ["name_prov", "name_prov", "name_unique", None, None, "name_prov"]


def test_crosswalk_marks_double_claims_ambiguous(istat):
    source = pd.DataFrame({"denominazione": ["Genova", "Genova"], "prov": ["GE", "GE"]})
    out = crosswalk(source, istat)
    assert out.match.tolist() == ["ambiguous", "ambiguous"]
    assert out.istat_code.isna().all()


@pytest.fixture(scope="module")
def tree():
    return json.loads((FIXTURES / "openbilanci_spese_genova_2019.json").read_text(encoding="utf-8"))


def test_flatten_keeps_every_node_and_flags_leaves(tree):
    flat = flatten(tree, "spese")
    # total, mission, programme, two titles
    assert len(flat) == 5
    assert flat.is_leaf.tolist() == [True, False, False, True, True]
    total = flat.iloc[0]
    assert (total["item"], total["year"]) == ("ccox-quadro-4-26", 2019)
    assert total.pc == pytest.approx(1780.52991206954)
    assert flat.iloc[3].label.startswith("SERVIZI ISTITUZIONALI, GENERALI E DI GESTIONE > ")


def test_wide_gives_one_row_per_municipality_year(tree):
    long = flatten(tree, "spese").assign(slug="genova-comune-ge")
    out = wide(long, leaves_only=True)
    assert len(out) == 1
    assert "spese:ccox-quadro-4-26" in out.columns
    assert "spese:ccox-quadro-4-2" not in out.columns


def test_detail_url_validates_arguments():
    url = detail_url("genova-comune-ge", "spese", 2019)
    assert url.endswith(
        "/armonizzati/bilanci/genova-comune-ge/spese/dettaglio.json?year=2019&type=consuntivo"
    )
    with pytest.raises(ValueError):
        detail_url("genova-comune-ge", "uscite", 2019)


def test_fetcher_reads_cache_without_network(tmp_path, tree):
    fetcher = Fetcher(tmp_path, delay=0)
    url = detail_url("genova-comune-ge", "spese", 2019)
    path = fetcher._path(url)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tree), encoding="utf-8")
    assert fetcher.get_json(url) == tree


def test_territories_adds_region_code():
    payload = {
        "items": [
            {
                "id": 1,
                "text": "Genova (GE)",
                "denominazione": "Genova",
                "prov": "GE",
                "cod_finloc": "GENOVA--1070340250",
                "slug": "genova-comune-ge",
            }
        ]
    }
    assert territories(payload).region_code.tolist() == ["07"]


def test_fetch_accounts_records_missing_accounts(tmp_path, tree):
    from itcorr.sources.openbilanci import fetch_accounts

    fetcher = Fetcher(tmp_path, delay=0)
    for section, body in (("spese", tree), ("entrate", None)):
        path = fetcher._path(detail_url("genova-comune-ge", section, 2019))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(body), encoding="utf-8")
    out = fetch_accounts(fetcher, ["genova-comune-ge"], [2019])
    assert out["item"].notna().sum() == 5
    assert out.loc[out["error"].notna(), ["section", "error"]].values.tolist() == [
        ["entrate", "no data"]
    ]
