# italy-corruption-ml

Research project: the Ash, Galletta and Giommoni (2025) corruption-prediction
pipeline, applied to Italian municipalities without random audits. Design in
docs/RESEARCH_DESIGN.md, sources in docs/DATA.md, label rules in docs/CODEBOOK.md,
open items in AUDIT.md.

## Rules

1. Never fabricate a number, result, reference or data source. A number in a
   document is produced by code in this repository, and the script is named next
   to it. If something cannot be verified, say so.
2. Simulated data is labelled SIMULATED wherever it is printed or quoted, and is
   never presented as evidence about Italy.
3. Unlabelled is not clean. Never turn missing labels into zeros silently; the
   positive-unlabelled assumption is always an explicit argument.
4. No resampling (SMOTE and similar). Imbalance is handled with class weights and
   thresholds, so predicted probabilities stay usable as rates.
5. Imputation, scaling and any fitted preprocessing are fitted on training rows
   only.
6. Report the paper's row split next to municipality and temporal splits; never
   report only the most flattering one.
7. Comparisons across seeds report mean and standard deviation, with fixed seeds.
8. When a doubt or defect is found, add an AUDIT.md item before or with the fix.
9. Everything written to disk is English. Explain non-obvious choices in the
   change itself: what was chosen, what was rejected, why.
10. The maintainer works on Windows (PowerShell), Python 3.13: call the venv
    interpreter directly (`.venv\Scripts\python -m pytest`).

## Commands

    pip install -e ".[dev]"
    pytest
    ruff check . && ruff format --check .
    python scripts/selective_labels_sim.py
