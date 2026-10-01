# Roadmap

Dates are targets, not promises. Course milestones (Economics of AI): essay
topic by 2027-01-01, essay due 2027-01-31. The research paper continues after.

| # | Step | Output | Depends on | Target | Status |
|---|---|---|---|---|---|
| 0 | Design, pipeline, simulation | `itcorr` core, `selective_labels_sim.py` | - | 2026-09-30 | done |
| 1 | Literature | docs/LITERATURE.md | PDFs | 2026-10-05 | 2 of 3 read; de Blasio et al. pending |
| 2 | **Warm-up replication on mafia dismissals** | the UIF / Campedelli design re-run with municipality-grouped and within-region evaluation, on 2016-2022 budgets | list of dismissals; full budget panel | 2026-10-31 | not started |
| 3 | Full budget panel 2016-2022 | features for about 7,900 municipalities | bdap-opendata domain, or a long OpenBilanci download | 2026-10-20 | sample verified (15 municipalities, 2019) |
| 4 | Corruption label, pilot | 200 hand-coded documents, two coders, kappa | judgments database domain; the maintainer's time | 2026-11-30 | codebook written |
| 5 | Corruption label at scale | LLM coding validated on the pilot | step 4 | 2026-12-20 | not started |
| 6 | Main model and selective-labels analysis | Ash et al. Table 2 and Figure 1 for Italy, three splits, within-area metrics | steps 3, 5 | 2027-01-15 | not started |
| 7 | Course essay | 5-10 pages on Ash et al. with this extension | step 6, or step 2 if 5 slips | 2027-01-31 | not started |
| 8 | Causal validation and policy simulation | Section III and IV analogues | step 6 | spring 2027 | not started |

Fallback: if the corruption label (steps 4-5) is not ready by mid-January,
the essay uses step 2, whose label is public and whose question (what does a
dismissal model learn, and how much of it is geography?) is the same.
