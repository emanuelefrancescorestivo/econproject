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

## Campedelli, Daniele and Le Moglie (2024), CEPR DP19322

"Mafia, Politics and Machine Predictions". **Abstract only.** Label:
mafia-related dismissals; predictors from local elections and budgets,
2001-2020; "up to 96%" of out-of-sample infiltrated municipalities, up to two
years ahead; a geographic difference-in-discontinuities on aid. Free on SSRN
(abstract id 4912204); the full text is needed before any claim about method.

## de Blasio, D'Ignazio and Letta (2022), Technological Forecasting and Social Change 184

"Gotham city. Predicting 'corrupted' municipalities with machine learning".
**Abstract only.** Label: corruption crimes in police archives (the label
closest to ours); prediction for 2012-2014. The journal version is paywalled; a
working-paper version exists as Sapienza DISS Working Paper 16/2020, "Predicting
Corruption Crimes with Machine Learning. A Study for the Italian
Municipalities". Iezzi and Pauselli report its best sensitivity and specificity
as 74% and 86.7% (p. 21).
