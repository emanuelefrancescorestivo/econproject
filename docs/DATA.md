# Data sources

A row is "verified" only after a file has been opened and its schema recorded here.

## Access log (2026-10-01, from the cloud development container)

| Source | Status |
|---|---|
| OpenBilanci (openbilanci.it) | **verified**: territory list and harmonised accounts JSON, see below |
| ISTAT municipality list (www.istat.it) | **verified**: `itcorr.sources.istat` |
| OpenBDAP portal (openbdap.rgs.mef.gov.it) | reachable; its data catalogue is on bdap-opendata.rgs.mef.gov.it, **blocked by the container's network policy** (domain not yet allowed) |
| Corte dei conti (www.corteconti.it) | reachable; the judgments database is on banchedati.corteconti.it, **blocked by the network policy** |
| SIOPE (www.siope.it) | reachable; query interface only, no bulk files found yet |
| Ministry of the Interior: Finanza Locale, elezionistorico | **refused by the site** ("Access Denied" to cloud addresses): download from a personal computer |
| ANAC open data (dati.anticorruzione.it) | **refused by the site's firewall** ("Request Rejected"): download from a personal computer |
| Supreme Court archive (www.italgiure.giustizia.it) | **connection reset by the site**: download from a personal computer |

## OpenBilanci, as verified

- Territories: `https://openbilanci.it/search/territori?q=` returns all 8,227
  municipalities known to the site, including abolished ones, with slug, name,
  province and the Ministry's finloc code.
- Accounts: `https://openbilanci.it/armonizzati/bilanci/<slug>/<entrate|spese>/dettaglio.json?year=Y&type=consuntivo`,
  2016 to 2022. A tree of items with euros and euros per inhabitant. In a
  random sample of 15 municipalities for 2019 (`scripts/fetch_openbilanci.py
  --sample 15 --years 2019`), 14 had accounts, each with the same 39 revenue
  and 367 expenditure nodes (31 and 272 leaves); one answered `null`.
- Crosswalk to ISTAT codes (same script): 7,609 territories match on name and
  province, 247 on a unique name within the same region, 1 on the first part
  of a bilingual name; 370 match nothing, mostly municipalities abolished by
  mergers (AUDIT item 9).
- Not yet known: whether the amounts are commitments (*competenza*) or cash
  (*cassa*) (AUDIT item 10). Licence CC BY-NC-SA 4.0; data is not committed.

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
