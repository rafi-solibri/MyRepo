# Cutshort daily 2026-08-11

## Counts
- Scanned: **1995** (newest + matchesfor + Hyd + skill scans)
- Qualifying: **4** (3 initial + 1 Tier3 stretch after classifier fix)
- Applied: **4**
- Already: 0
- Failed/blocked (apply): **0**
- External: 0
- Q answered correctly (option IDs): **1** (Bigmantra 3/3)
- Q locked-wrong (free-text stuffed into MCQ; 400 on rewrite): **3** — count as failures
- Q already-submitted (historical unique audit): **27**
- Q locked-empty (historical unique): **324**
- Awaiting listed: **356**
- Failures (locked-wrong Q + locked-empty): **327** (apply Failed≠0 once Q failures counted)

## Applied
- T1 EDI Architect @ i2b Technologies Pvt Ltd (40L) `6a5091fd7c8063fb8eb465ce` via=api_no_ui_button — thread `6a7a9fcb27864a9f05a90f59` Q **locked-wrong** 8/8
- T1 AI Architect @ KnackLabs (35L Hyd) `6a79ae56ce083ab95126b611` via=api_no_ui_button — thread `6a7a9d42eee4843c27b24b48` Q **locked-wrong** 2/2
- T2 Senior Software Developer @ NeoGenCode Technologies Pvt Ltd (35L) `67bd7a6ed78a650029b708ac` via=api_no_ui_button — thread `6a7a9e81e0d9c4c3956c7a35` Q **locked-wrong** 3/3
- T3 Fullstack AI Applied Engineer @ Bigmantra (50L remote) `6a3e7348ebc58e0483734112` via=api — thread `6a7aa44ba423e93b35647372` Q **OK** 3/3 (location OK / immediate / Yes on ₹30–50L)

## Why UI said blocked
Chrome hit Cloudflare Turnstile on job pages; Apply button missing. Durable runner now falls back to `POST /sendreply/jobsignal`.

## Questionnaire fix (shipped)
Cutshort nests MCQ under `question.title` + `question.options[].label` (not top-level `questionString` / `responseOptions`). Old picker saw zero options → free-text fallback → `screeningSubmitted:true` locked wrong answers (400 rewrite). Helper + `daily_apply.js` now read nested shape and only submit after non-empty verify.

## Inventory note
Hyd/remote ≥35L pool ~95 mostly hard title-skips (PM/Data/QA/Mobile/Workday/Shopify/intern vanity) or no-tier non-stack roles. No further Tier1/2/3 left after these 4.

## Runner changes
- API apply fallback when UI blocked / no textarea
- Title-first Tier1 (no Salesforce skill veto)
- Broader Tier3 stretch (incl. Generative AI / fullstack)
- `matchesfor` scan included
- Per-apply Q without double-counting audit totals
