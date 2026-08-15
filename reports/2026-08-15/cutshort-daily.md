# Cutshort daily 2026-08-15 (post-fix re-run) <!-- pragma: allowlist secret -->

**POST_FIX_RERUN=1** on merged `main` @ `3fc57c3` (`fix(ats): use the one env password for every Workday/ATS helper` #163).

Earlier original daily and prior same-day re-runs did **not** apply with this ATS password alias. This session pulled `main`, ran preflight + Chrome CDP (synced portal profile), and executed the durable `daily_apply.js` helper with `Rafi_Resume.docx`.

Login: OK (candidate dashboard, live CDP, portal auth cookie present). Resume: `/workspace/resumes/Rafi_Resume.docx`.

## Counts
- Scanned: **3193** (`pageSize=50`; newest total_count=3222)
- Qualifying: **0**
- Applied: **0** (none invented)
- Already (this pass): 0
- Failed/blocked (apply): 0
- External: 0 (no qualifying company-site cards to exercise #163)
- Q answered: **1** | already-submitted: 36 | locked-empty: **323** (historical API locks, not same-day apply failures) | verify-empty: 0
- Awaiting listed: 363
- Failures (apply + locked-empty + verify-empty): **323**
- Same-day apply failures: **0**

Skip taxonomy: `location=212` `skip_title=752` `ctc_under_35=1162` `no_tier_match=53` `exp_max_low=1014`

## Already applied earlier today (skip — do not re-apply)
Documented by the first post-fix re-run from the original morning second pass (those listings are gone from `/findjobs`):

| ID | Title | Company |
|----|-------|---------|
| `6a1fd51dd7bf645877d57db8` | Principal Engineer, Salesforce Health Cloud | Unique Occupational (38L) |
| `6a4b58ed80b936a4374760b4` | Senior Full-Stack Engineer | Recro (38L) |
| `6a2146d3654875adb93e1546` | Sr. AI Ops Engineer | Fx31labs (45L) |

## Why 0 applies (not invented)
Hyd/remote Architect / Tech Lead / EM / Senior .NET cards that remain list **max CTC 12–25 LPA** (hard-skip under 35L).

`ctc>=35` + Hyd/remote leftovers are title-first wrong fits, inspected live after this run (50 near-miss / 53 `no_tier_match`): Customer Success, CAD/CAM, PHP/Symfony, IT Support Director, MDM/Oracle, Product Marketing, Pre-Sales Solutions Engineer, Ontologist, Salesforce ServiceMax, ServiceNow, Data Scientist / ML IC, UX/UI, Database Developer, SailPoint, Robotics, sales/Regional Partner, AWS Cloud Engineer (Hyd IC troubleshooting 35L), Frontend React IC, Backend Rust IC.

No new Hyd/remote Architect / Tech Lead / EM / Principal / Staff / Senior .NET card at ≥35L. `#163` ATS password alias was loaded (`NAUKRI_WORKDAY_PASSWORD` → `WORKDAY_PASSWORD` / `ATS_PASSWORD`) but unused because there was no external ATS apply.

Did **not** loosen the 35L floor. Did **not** launch another post-fix re-run (no new code-fixable blocker; same-day portal re-run count is 4 including this job, cap 5).

## Applied
_None_

## Questionnaires
- Submitted **1** pending screening (`6a800d2379188d65c5328309`, 4 answers) with the durable `questionnaire.js` payload (verify-before-`screeningSubmitted`).
- Historical `locked-empty`: 323 (cannot be unlocked in code).

## Failed applies
_None_

Artifacts: `/opt/cursor/artifacts/` portal daily-run JSON and `/tmp/` run `stats.json`
