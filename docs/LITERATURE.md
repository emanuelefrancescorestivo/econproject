# Closest literature: reading notes

Notes are written from the full text when it was read, and say so. Page numbers
refer to the PDF as published. Abstract-only entries are marked and must not be
used for claims about method.

## Iezzi and Pauselli (2025), UIF Quaderni dell'antiriciclaggio, Analisi e studi n. 27

"The risk of mafia infiltration in Italian municipalities: Statistical and machine
learning evidence from financial information". **Read in full** (2026-10-01).

What they do:

- **Label**: municipalities dissolved for mafia infiltration (art. 143 TUEL); the
  infiltration years are the years the dissolved council was in office, with a
  June cut-off for the first and last year (p. 11). 1991-2022: 368 dissolutions,
  267 municipalities, 89% in Campania, Calabria and Sicily (p. 8). In the
  2016-2021 sample: 221 dissolved municipality-years against 6,571 control
  municipality-years, about 1 to 29 (Table 4, p. 14).
- **Predictors**: harmonised year-end certificates from BDAP, 2016-2021 (p. 8);
  spending *commitments* only, following Di Cataldo and Mastrorocco (2022), as
  shares of total spending in 9 grouped missions (p. 9); revenue-collection
  efficiency and autonomy indicators (Table 2); 48 of the 55 indicators of the
  "Piano degli indicatori" (p. 11); socio-economic controls including
  confidential UIF data (p. 12).
- **Label noise is named explicitly** (pp. 12-13): non-dissolved municipalities
  may be infiltrated. Their remedy: draw controls only from provinces whose
  share of firms potentially linked to organised crime (a confidential UIF
  mapping) is below the median, and match each dissolved municipality to its
  100 nearest non-dissolved ones on socio-economic variables (p. 13).
- **Model**: XGBoost; 80/20 split stratified by label and clustered by
  municipality, so no municipality is in both sets (p. 18); replication-based
  oversampling of positives to a 1:1 balance in training folds only (p. 18);
  random search over 2,500 hyperparameter sets, 5-fold CV on AUC (pp. 18-19).
- **Results**: test AUC 98.22%; at cut-off 0.5, sensitivity 60.0%, specificity
  99.62%, precision 84.38% at the test set's 1:29 balance, which they re-express
  as 44.16% at an assumed 1:200 population balance (Table 8, p. 20). Reported
  comparison: Campedelli et al. (2024) sensitivity 96.4%, specificity 87.8%,
  precision 6.2% (p. 21).
- **Scores by region, 2021** (Table 10, p. 22): mean risk 0.0 in every
  northern region; 29% Campania, 46% Calabria, 45% Sicily.
- **Validation** (Section 7): within Campania, Apulia, Calabria and Sicily, the
  score is associated with the presence of OC-linked firms and with incomplete
  procurement reporting to ANAC (fractional logit with controls).

What this means for this project:

1. **Within-area discrimination is untested by construction.** Negatives come
   only from below-median provinces, so the training data contain no
   non-dissolved municipality from the high-incidence provinces where the
   dissolved ones are. The 98% AUC measures, at least in part, the separation of
   two kinds of province. Our within-area evaluation and the region-only
   benchmark (RESEARCH_DESIGN section 4) test exactly what their design cannot.
2. **Their scores are not probabilities.** Training at a 1:1 replicated balance
   inflates predicted risk (they correct precision for prevalence, but Table 10
   reports raw scores as "an indicative measure of the probability"). A
   targeting simulation in the Ash et al. style needs calibrated scores; we do
   not resample (AUDIT item 7).
3. **Their label is infiltration, ours is corruption.** Different event, so the
   two risk scores can be compared as validation of each other, not as
   substitutes.
4. **Commitments, not cash.** Their choice and its reason (p. 9) is the
   answer to our AUDIT item 10, once OpenBilanci's figures are confirmed to be
   commitments.
5. Their within-South validation (p. 25, Table 11): mean risk 0.45 without and
   0.42 with an OC-linked firm, medians 0.17 and 0.76. The means go the
   "wrong" way while the medians and the conditional regression go the right
   way: the association is not a simple shift.

## Campedelli, Daniele and Le Moglie (2024), CEPR DP19322 / SSRN 4912204

"Mafia, Politics and Machine Predictions", version of July 22, 2024. **Read in
full** (2026-10-01, text extracted from the SSRN PDF; page numbers are the
paper's own).

What they do:

- **Label**: mafia-related dismissals, coded 1 in the dismissal year and every
  earlier year of the same electoral term (p. 10). Revoked dismissals are
  coded 0 (p. 18, fn. 30). 855 positives in 105,628 training observations,
  0.83% (p. 11).
- **Predictors**: Ministry of the Interior data, 2001-2020: seven electoral
  variables, six ideology dummies, 22 spending categories by current and
  capital account turned into shares, per-head amounts and lags (pp. 9-10),
  plus regional dummies (Table S4); 223 features in all (fn. 31).
- **Split**: 70/30, stratified on the label, at the municipality-year level
  (p. 13). The same municipality, and the same electoral term, can be in both
  sets, while the label is constant within a term and features include lags.
  A temporal split (test from 2015, 2017 or 2019 on) gives similar numbers
  (Table S5), but no split keeps municipalities apart.
- **Model selection**: nine algorithms, 1,576 candidates; the criterion "was
  based on maximizing out-of-sample recall (i.e., recall measured on the test
  set)" (p. 14), with 5-fold CV described in the same paragraph.
- **Imbalance**: SMOTE, ADASYN, SMOTE+Tomek; best model XGBoost + ADASYN with a
  positive-class weight of 50 (fn. 23). Mean predicted risk 0.15 against a
  0.83% base rate (fn. 33): the scores are not probabilities.
- **Results**: test recall 0.96 at threshold 0.5, ROC-AUC 0.92, precision 0.06
  (pp. 14-15). Top 5% of risk each year: precision 14.6%, recall 88.9% (p. 19).
- **Robustness that matters for us** (Tables S4, S6): without regional dummies
  AUC falls from 0.922 to 0.861; Southern regions only, AUC 0.84; *within
  dissolved municipalities only* (which years are infiltrated), AUC 0.61-0.62;
  cross-sectional averages, AUC 0.67 (0.82 with ADASYN).
- **Selective labels are named** (pp. 2-3, 12): false positives may be
  undetected infiltration; indirect support from mafia murders and attacks on
  politicians among "suspected" municipalities (Section 4.4).
- **Second part**: the predicted index as outcome in a geographic
  difference-in-discontinuities on 2007-2013 EU funds: +11 to 14 points.

What this means for this project:

1. They already report a South-only model and a no-region model, so "the model
   is a map" is partly answered for mafia dismissals: geography adds about 0.06
   of AUC. What nobody reports is a split that keeps municipalities apart, and
   their within-dissolved exercise (AUC about 0.62) suggests that telling
   *when* is much harder than telling *where*.
2. A municipality-grouped re-run of their design, on the same label, is a
   cheap and informative first empirical result (ROADMAP step 2).
3. Their index is the Ash et al. Section III idea applied to Italy (predicted
   outcome in a causal design); the generated-outcome inference problem applies
   to it too.

## de Blasio, D'Ignazio and Letta (2022), Technological Forecasting and Social Change 184

"Gotham city. Predicting 'corrupted' municipalities with machine learning".
**Abstract only.** Label: corruption crimes in police archives (the label
closest to ours); prediction for 2012-2014. The journal version is paywalled; a
working-paper version exists as Sapienza DISS Working Paper 16/2020, "Predicting
Corruption Crimes with Machine Learning. A Study for the Italian
Municipalities". Iezzi and Pauselli report its best sensitivity and specificity
as 74% and 86.7% (p. 21).
