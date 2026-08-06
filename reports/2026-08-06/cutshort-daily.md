# Cutshort daily — 2026-08-06

Candidate: Rafi Ahmed (Solutions Architect / Technical Lead, Hyderabad, 52→65 LPA, immediate)

## Counts

| Metric | Count |
|--------|------:|
| Jobs scanned (unique) | 1158 |
| **Applied** | **1** |
| Already applied | 0 |
| Failed / blocked | 0 |
| External ATS | 0 |
| Questionnaires filled (verified) | **1** |
| Questionnaires locked-empty (pre-existing) | ~348 awaiting; sample shows most already `screeningSubmitted` with empty answers from prior runs |
| Remaining unsubmitted (pages 1–20) | 0 |
| Chat follow-ups | Prior aborted sweep messaged many locked threads; today's Incubyte thread already had screening prose before Q API fill |

## Applied

1. **Software Craftsperson Node/Typescript/ReactJS - III @ Incubyte** (Tier 3 stretch, Remote only, hideSalary / Best in industry) — confirmed via `POST /sendreply/jobsignal` → already-made; questionnaire **6/6 filled + submitted** (52/65 LPA, immediate).

## Hard skips / near-misses (not applied)

- Senior Solution Architect – Google Cloud @ Staffnixcom — Hyd listed, **47 LPA max** (&lt; 50 hard skip)
- Principal Data Engineer @ Mitratech — remote 52L but RoR/data-eng weak fit
- Chief Agentic Quality Architect @ FAiHr — QA/quality tooling skip

## Inventory note

Tier-1 SA/Tech Lead/EM Hyd/remote with listed max ≥50 LPA remains **extremely scarce**. Most Hyd/.NET rows are below CTC gate or wrong specialty.

## Ops fix learned today

Free-text screening answers must use `responseStringArray: ["…text…"]` (not `responseString`). Verify via `loadthread-v2` before `screeningSubmitted: true`.
