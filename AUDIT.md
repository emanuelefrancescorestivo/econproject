# Audit log

Open items, known limitations and decisions. Add an item when a defect or doubt
is found, before or with the fix.

1. **Novelty.** Iezzi and Pauselli (2025) and Campedelli et al. (2024) read in
   full (docs/LITERATURE.md). Neither evaluates with municipalities kept apart
   between training and test; the first takes negatives only from
   low-incidence provinces, the second splits municipality-years at random and
   selects models on test-set recall. Within-area discrimination of *when*,
   not *where*, is the open question. de Blasio et al. (2022) still known from
   the abstract only. Status: open for that one.
2. **Data access.** OpenBilanci and ISTAT verified; the rest is logged in
   docs/DATA.md. Status: open for the label sources.
3. **abuso d'ufficio.** Excluded from the narrow label as closer to "broad"
   mismanagement; its 2024 repeal is recalled, not checked against the statute.
   Status: open.
4. **Inner selection metric.** The paper does not state it; AUC-ROC is used.
   Status: decision, revisit if the replication package says otherwise.
5. **Refit without early stopping.** The outer refit uses the mean best iteration
   of the inner folds. Status: decision.
6. **Split-count importance** (the paper's measure) favours continuous,
   high-cardinality features. Report SHAP alongside. Status: open, SHAP not yet
   added.
7. **No resampling.** SMOTE and similar are not offered: they distort
   probabilities, which the policy simulation reads as rates
   (van den Goorbergh et al., JAMIA 2022). Class weights only. Status: decision.
8. **2005-2015 accounts.** OpenBilanci offers them under the pre-harmonisation
   scheme, through a route not reachable from the development container. The
   first sample is therefore 2016-2022, which also avoids the 2015-2016
   accounting break. Status: open.
9. **Abolished municipalities.** 370 OpenBilanci territories have no ISTAT code
   in the current list, mostly municipalities merged since. A panel that spans a
   merger needs ISTAT's register of administrative changes. Status: open.
10. **Amounts.** Not yet established whether OpenBilanci's harmonised figures are
    commitments or cash; compare one municipality against its published
    *rendiconto* before modelling. Iezzi and Pauselli use commitments only, for
    a stated reason (docs/LITERATURE.md); we follow unless there is a reason not
    to. Status: open.
11. **Crosswalk false matches.** A name-only match first mapped Calliano (AT),
    since renamed, onto Calliano (TN). Fixed by requiring the same region (from
    the finloc code); covered by a test. Status: fixed.
