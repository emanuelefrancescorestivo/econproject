# Audit log

Open items, known limitations and decisions. Add an item when a defect or doubt
is found, before or with the fix.

1. **Novelty not yet established.** The three closest Italian papers (Campedelli,
   Daniele and Le Moglie 2024; Iezzi and Pauselli 2025; de Blasio, D'Ignazio and
   Letta 2022) are known from abstracts only; full texts were unreachable from the
   development container. Status: open. Read them before writing any claim of
   contribution.
2. **No data verified.** Every source in docs/DATA.md is unverified. Status: open.
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
