# Research design

Working title: **Machine-predicted corruption without random audits: evidence from
Italian municipalities.**

## 1. Question

Ash, Galletta and Giommoni (2025, *AEJ: Economic Policy* 17(2): 162-193) show that a
gradient-boosted classifier trained on 797 municipal budget variables predicts the
outcome of Brazil's *random* federal audits (AUC-ROC 0.781), that the predicted
measure responds to causal shocks as audited corruption does, and that audits
targeted by predicted risk would detect about 80% more corrupt municipalities than
the lottery.

Their design rests on a feature Italy lacks: the labels come from a lottery, so a
municipality's chance of being labelled does not depend on anything the model sees.
Every Italian corruption label is the end of a *detection* process (a complaint, a
prosecutor, a newspaper). This project asks:

1. Can the Ash et al. pipeline predict corruption in Italian municipalities from
   budget data, with labels built to match theirs as closely as Italy allows
   (narrow corruption offences, dated to the budget years of the conduct)?
2. How much of what such a model learns is corruption, and how much is detection?
3. Do the paper's validation logic (causal responses) and policy conclusions
   (targeting, fairness) survive when labels are selective?

Question 2 is the contribution. The existing Italian ML work predicts
mafia-related council dismissals (Campedelli, Daniele and Le Moglie, CEPR DP19322,
2024; Iezzi and Pauselli, UIF Quaderno 27, 2025) or corruption crimes in police
records (de Blasio, D'Ignazio and Letta, *Technological Forecasting and Social
Change* 184, 2022). Iezzi and Pauselli, read in full, name the problem of
undetected positives among the negatives and answer it by taking negatives only
from provinces with a low incidence of organised-crime-linked firms. That removes
the negatives a model would most need to tell apart from the positives, so how
well their 98% AUC holds *within* the affected areas is untested by design
(docs/LITERATURE.md). The other two papers must still be read in full (AUDIT
item 1) before the claim is made in writing.

## 2. Mapping to the paper

| Ash et al. (2025) | This project | Status |
|---|---|---|
| Label: narrow corruption found by a random CGU audit, per budget year examined | Detected narrow-corruption event (docs/CODEBOOK.md), per year of conduct; `labels.py` | code done, data not collected |
| Unaudited municipality-years unlabelled | No event is *unlabelled*, not clean; negatives only by explicit assumption | code done |
| 797 budget variables, 2001-2012, mean imputation | Municipal financial statements (docs/DATA.md); accounting break in 2015-2016 | sources to verify |
| XGBoost, nested 5-fold CV, 288-cell grid, early stopping | `models.py`, same grid and procedure | code done, tested on synthetic data |
| Baselines: modal guess, OLS, Lasso, elastic-net logit | `models.baseline_oof` | code done |
| Row split; municipality split in the appendix | `splits.py`: row, group, temporal | code done |
| Accuracy, AUC, F1; calibration plot | plus average precision, precision/recall at k, Brier (`metrics.py`) | code done |
| Feature importance vs mentions in audit reports | Importance (and SHAP) vs mentions in judgments or case texts | not started |
| RDD on FPM population thresholds | Italian population thresholds (section 5) | not started |
| Event study of audits | Event study of detected episodes on neighbours and on the municipality | not started |
| Targeting, fair targeting by party | `policy.py`; groups: party, macro-area | code done |

## 3. Label

Faithful to the paper means: narrow corruption, attached to the budget years in
which it happened, with an explicit unlabelled state. The codebook fixes the
offences (peculato, concussione, corruzione, induzione indebita, traffico di
influenze illecite, turbativa d'asta), the stages (investigation, indictment,
conviction) and the conduct period. Candidate sources are in docs/DATA.md; the
choice between them is the first data decision and depends on access.

Because the stage matters, labels are built at three thresholds (investigation,
indictment, conviction) and results are reported for each. A finding that holds
only at the investigation stage is a finding about prosecutors.

## 4. Selective labels

Let c be true corruption, d detection given corruption, and y = c·d the observed
label. Brazil's lottery makes d independent of the budget. In Italy d depends on
the prosecutor's office, local media and the region, all of which a budget can
reveal. A model trained on y then ranks by P(c)·P(d | x), and the out-of-sample
AUC a researcher computes is measured against y, not c.

`scripts/selective_labels_sim.py` checks this on simulated panels. Its output is a
design check, not a result, and is reproduced by running the script. In the
selective scenario the AUC against detected labels rises while the AUC against
true corruption falls: the metric a researcher can see moves the wrong way.

Planned responses, in order of cost:

1. **Benchmarks that expose "where", not "who".** A model on region, province or
   prosecutor-office dummies alone. If the budget model barely beats it, the budget
   model is a map.
2. **Within-area evaluation.** AUC and precision at k within each region and each
   prosecutor-office district.
3. **Detection controls.** Measures of detection intensity (prosecutor-office
   caseload, local press coverage) as features or strata, so ranking within equal
   detection is possible.
4. **Positive-unlabelled learning and selective-labels methods** (Elkan and Noto,
   KDD 2008; Lakkaraju et al., KDD 2017), with the assumptions stated.
5. **External validation where detection is closer to random.** Candidates: the
   2011-2012 switch to randomly drawn municipal auditors (Vannutelli, NBER WP
   30644) as a source of variation in monitoring; checks where a label comes from
   an inspection rather than a complaint.

## 5. Causal validation (Section III of the paper, Italian version)

The paper argues that its measure captures corruption because it responds to known
causal shocks. Italian candidates, to be checked for data availability:

- population thresholds that change municipal resources or rules (the Domestic
  Stability Pact at 5,000 inhabitants, Grembi, Nannicini and Troiano, *AEJ: Applied*
  2016; mayors' wages, Gagliarducci and Nannicini, *JEEA* 2013);
- the staggered introduction of randomly drawn auditors (Vannutelli);
- spillovers of a detected episode or a council dismissal to neighbouring
  municipalities (Galletta, *Journal of Urban Economics* 101, 2017, finds that
  neighbours' investment falls after a dismissal).

The prediction error must be tested for correlation with each instrument, as the
paper does. Inference with a predicted outcome uses bootstrap over prediction
draws (as in the paper) and, where it applies, prediction-powered inference.

## 6. Policy simulation

As in Section IV, with two changes: evaluation within area as well as nationally,
and fairness by party *and* macro-area. The cost of parity is measured, not assumed:
in Brazil it was small (0.868 against 0.871); where base rates differ as much as
they may between Italian macro-areas it need not be.

## 7. Risks

- **Label access.** If no source gives municipality-level, dated, narrow events at
  scale, the project falls back to police-archive data under a data agreement (as
  de Blasio et al. used), or narrows to a region.
- **Budget comparability** across the 2015-2016 accounting harmonisation.
- **Novelty.** Section 1's claim stands or falls on reading the three Italian
  papers in full.
