# italy-corruption-ml

Predicting corruption in Italian municipalities from budget data, following
Ash, Galletta and Giommoni, "A Machine Learning Approach to Analyze and Support
Anticorruption Policy", *AEJ: Economic Policy* 17(2), 2025.

The paper learns from Brazil's **random** audits. Italy has none: every corruption
label is the end of a detection process. This project reproduces the paper's
pipeline on Italian data and asks how much a model trained on *detected* corruption
learns about corruption, and how much about detection. See
[docs/RESEARCH_DESIGN.md](docs/RESEARCH_DESIGN.md).

## Status

- Done: label construction, outer splits, the paper's nested-CV XGBoost and
  baselines, metrics, targeting and fair-targeting simulation, a synthetic
  selective-labels generator and Monte Carlo. Tested on synthetic data only.
- Data: municipal budgets 2016-2022 from OpenBilanci with the ISTAT crosswalk
  (`scripts/fetch_openbilanci.py`), verified on a sample. Labels not yet
  collected; access status per source in [docs/DATA.md](docs/DATA.md).
  **There are no results about Italy yet.**

## Commands

    pip install -e ".[dev]"
    pytest                                     # unit tests, synthetic data, a few seconds
    ruff check . && ruff format --check .
    python scripts/selective_labels_sim.py     # design check on SIMULATED data, ~1 min
    python scripts/fetch_openbilanci.py --sample 20 --years 2019   # real budgets, cached in data/

On Windows (PowerShell), call the venv interpreter directly:
`.venv\Scripts\python -m pytest`.

## Layout

| path | role |
|---|---|
| `src/itcorr/labels.py` | detected events to municipality-year labels, with an explicit unlabelled state |
| `src/itcorr/splits.py` | row (the paper's), municipality and temporal splits |
| `src/itcorr/models.py` | XGBoost with the paper's 288-cell grid, nested CV, Table 2 baselines |
| `src/itcorr/metrics.py` | Table 2 metrics plus precision/recall at k, average precision, calibration |
| `src/itcorr/policy.py` | Section IV: random, targeted and fair audits |
| `src/itcorr/simulate.py` | synthetic panels with region-dependent detection |
| `src/itcorr/sources/` | OpenBilanci budgets, ISTAT list and crosswalk |
| `docs/ROADMAP.md` | steps, dependencies, target dates |
| `docs/LITERATURE.md` | reading notes on the closest Italian papers |
| `docs/CODEBOOK.md` | how a document becomes a corruption event |
| `AUDIT.md` | open questions, known limitations, decisions |
