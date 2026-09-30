# Event codebook

One record per episode: a set of facts about one municipality's administration that
a source document describes as a corruption offence. The fields match
`itcorr.labels.CorruptionEvent`.

| Field | Rule |
|---|---|
| `istat_code` | Six-digit ISTAT code of the municipality whose administration is involved (not where the court sits). One record per municipality if several are involved. |
| `conduct_start`, `conduct_end` | First and last calendar year of the alleged conduct as stated in the source. If only one year is stated, both equal it. If no year is stated, the record is kept but excluded from labels, and the count of such records is reported. |
| `offences` | Criminal-code articles charged or found, as strings ("319", "353-bis"). Narrow set in `labels.NARROW_OFFENCES`. |
| `stage` | Furthest stage the source documents: `investigation` (investigation or precautionary measure reported), `indictment` (committal to trial), `conviction` (first-instance or later). |
| `acquitted` | True if every defendant was acquitted or the case dismissed. |
| `source_id` | Stable identifier of the document (URL, judgment number, archive id). |

Who counts as "the administration": elected officials (mayor, council members,
executive) and municipal employees acting in their role. Private parties alone,
without an official of the municipality, do not make an event.

Coding protocol:

1. Two people code the same random sample of at least 200 documents by hand;
   report agreement (Cohen's kappa) per field.
2. An LLM codes the same sample; report agreement with the hand-coded consensus
   per field. The LLM is used at scale only if agreement on `istat_code`,
   conduct years and `offences` is close to human-human agreement.
3. Every automatically coded record keeps its `source_id`, so any label can be
   traced back to its document.
