# Cutshort daily run — 2026-08-05

Candidate: Rafi Ahmed (Solutions Architect / Technical Lead, Hyderabad, immediate, 52→65 LPA)

## Counts

| Metric | Count |
| --- | ---: |
| Applied (confirmed) | 6 |
| Already applied | 0 |
| Failed / blocked | 0 |
| Questionnaires answered (new today) | 5 |
| Pre-existing awaiting threads (already screeningSubmitted) | ~331 left untouched |

Session: Candidate login was active (dashboard + apply path worked).

## Applications (newest-first feed + skill/Hyderabad scans; Tier 2 then Tier 3)

True Tier‑1 Solutions/Tech Lead/EM roles at suitable CTC were scarce in the active feed (mostly Associate/low-YOE/low-CTC). Applied strongest Tier‑2/Tier‑3 fits:

1. **Senior Platform & Site Reliability Engineer** — FAiHr — To RK — note + follow-up sent; questionnaire answered  
2. **Principal DevOps Engineer** — Securin Labs — To Anitha — note + questionnaire  
3. **Azure DevOps + Python** — Wissen Technology — To Shakthi — note + questionnaire  
4. **Lead Java Developer (Bangalore / Mumbai)** — Wissen Technology — To Khushboo — note + questionnaire  
5. **Java Fullstack Lead** — Wissen Technology — To Annie — note + questionnaire  
6. **Full Stack Engineer** — Majoris/VRIZE posting — To AMIT — note sent; no questionnaire yet  

## Skipped (examples)

- QA/SDET, junior/intern/associate, AutoCAD/architecture interiors  
- Workday/Dynamics/SAP-heavy and pure data-architect roles  
- Clear low YOE gates (e.g. Partner Solutions Architect 3–6 yrs)  
- Clear low-CTC / weak-fit titles (Tech Lead @ 18L, EM @ 20L, many mid-level .NET roles)

## Notes

- Apply API: `POST /sendreply/jobsignal` (navigate one `all-jobs?jobid=` URL at a time).  
- Questionnaire API: `GET /conversations-v2/candidate?...&convo_status=awaiting` → `GET /loadthread-v2/{id}` → `POST /update-message/{messageId}` with `screeningSubmitted: true`.  
- Many older awaiting threads already have `screeningSubmitted: true` (UI shows “Questionnaire submitted!”); API rejects re-submit.
