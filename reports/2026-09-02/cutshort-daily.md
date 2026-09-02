# Daily apply 2026-09-02 (post-fix re-run)

POST_FIX_RERUN=1 on `main` at `b34a0ac` (includes merged #312). Morning cron applied with pre-#312 code; this job re-ran the durable helper so today's apply/email path used merged `main`.

Automation: https://cursor.com/automations/d6ba8b9d-9094-11f1-ba66-0e7d0216e441

## Day totals (do not invent)
- **Applied today (real): 1** — cron `bc-4984a312-20d2-4bd5-bbae-7e861d91d9c6`
- This post-fix session applied **0** (skip already-applied; no new qualifying inventory)
- Login: OK (candidate dashboard + auth cookie)

## Cron run (morning automation)
- Scanned: **3333** | Qualifying: **1** | Applied: **1**
- Q answered: **1** | already-submitted: 50 | locked-empty: **316** (historical; not same-day apply failures)
- Tailored resumes: built 1 | profile uploaded 1
- Applied:
  - T1 ServiceNow Architect @ Neev Systems (35L) `6a9697b522eddb1a780350cc` via=`api_no_ui_button`

## This post-fix re-run (`bc-f3e2263c-8449-4a93-87d9-ad9260045f67`)
- Preflight: OK (resume rebuilt from master `Rafi_Resume.docx`)
- CDP login: OK
- Scanned: **3339**
- Qualifying: **0**
- Applied: **0**
- Already: 0 (Neev Systems id no longer in find-jobs — already submitted this morning)
- Failed/blocked: 0
- External: 0
- Q audit skipped (0 applies this session; historical locked-empty cannot be unlocked)
- Skip taxonomy: `ctc_under_35=1251` `exp_max_low=1020` `skip_title=789` `location=233` `no_tier_match=46`
- Artifact: `/opt/cursor/artifacts/` home JSON (`source=cloud-postfix-rerun`)

## Classifier check (no new code fix)
Live CDP sample (~2700 cards) of Architect / Tech Lead / EM / .NET-looking titles:

| Bucket | Count | Verdict |
|---|---|---|
| QUALIFY after current filters | **0** | Inventory empty after morning apply |
| location | 37 | Bangalore / Pune / Mumbai / NCR / other cities, `remote_not_okay` — correct Hyd/remote skip |
| ctc_under_35 | 112 | Listed max under 35L — hard skip |
| skip_title | 69 | Data architect/engineer, QA, SAP, trainee — title-first skip |
| exp_max_low | 23 | Listed max exp under 6 — correct |
| no_tier_match (full scan) | 46 | Sales / data-science / PHP / ServiceNow-dev / marketing — not Architect/Lead/.NET |

AI-headline vs posted-headline recovered only 2 weak cards (Full Stack AI Engineer; Lead Database Migration) — not truthful .NET/architect applies. Remote-location false-skip count: **0**.

No new code-fixable blocker. Did not loosen filters to invent applies. Did not launch another post-fix re-run (this is re-run **2** of 5 for 2026-09-02 IST; earlier re-run `bc-3c2e0959` was triggered by Indeed #309, not a helper fix for this portal).

## Failed applies
_None_
