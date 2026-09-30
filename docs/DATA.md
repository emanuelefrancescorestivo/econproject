# Data sources

Status as of the first commit: **nothing has been downloaded or inspected.** The
development container's network policy blocked every Italian government domain
listed below, so formats, coverage and licences are unverified. Each row becomes
"verified" only after a file has been opened and its schema recorded here.

## Predictors: municipal budgets (the paper's X)

| Source | Holder | Expected content | To verify |
|---|---|---|---|
| Certificati di conto consuntivo | Ministero dell'Interno, Finanza Locale | Year-end accounts per municipality, detailed items | years covered, file format, item codes over time |
| BDAP | MEF, Ragioneria Generale dello Stato | Harmonised budgets after d.lgs. 118/2011 | first usable year, bulk download |
| SIOPE | MEF / Banca d'Italia | Payments and receipts by code, per entity | municipal coverage, frequency, history |
| OpenBilanci | openpolis | Harmonised historical series built from the above | licence, how items were mapped |

Known issue: the accounting harmonisation (d.lgs. 118/2011, in force for
municipalities around 2015-2016) changes the chart of accounts. Options: separate
models before and after, a crosswalk, or a post-2016 sample only. Decide after
seeing the items.

## Label: corruption events

| Source | Unit | Pros | Cons |
|---|---|---|---|
| Court of Auditors (Corte dei conti) judgments | case | public texts, municipal administrators, dated conduct | fiscal damage, not always a corruption offence |
| Supreme Court criminal judgments (SentenzeWeb) | case | final, offence articles stated | long lags; coverage of the free archive to check |
| News archives (national agencies, local press) | episode | early, broad | coverage depends on media attention: another selection layer |
| Police archive (SDI) crime data | municipality-year | what de Blasio et al. used | not public; data agreement needed |
| ANAC supervisory decisions | contract / entity | procurement-specific | not a criminal finding |

Text sources are coded into events with the codebook (docs/CODEBOOK.md), by hand
on a sample first, then with an LLM validated against the hand-coded sample.

## Other covariates

- Mayors, parties and terms: Anagrafe degli amministratori locali (Ministero
  dell'Interno).
- Election results: Eligendo / historical election archive (Ministero dell'Interno).
- Population, demographics: ISTAT. Taxable income by municipality: MEF.
- Mafia-related council dismissals (art. 143 TUEL): used as a covariate and a
  robustness label, not as the main label.

## Domains to allow in the cloud environment

finanzalocale.interno.gov.it, dait.interno.gov.it, elezionistorico.interno.gov.it,
openbdap.rgs.mef.gov.it, siope.it, openbilanci.it, dati.anticorruzione.it,
istat.it, corteconti.it, italgiure.giustizia.it.
