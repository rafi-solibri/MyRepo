# Daily apply report 2026-08-30 (same-day post-fix re-run)

POST_FIX_RERUN=1 on merged `main` (`fa8b17f` / PR 293). Morning cron (`bc-11077a81-24b0-4041-aa45-85aedcc03752`, draft PR 288) also applied **0** — this re-run executed the durable helper with the merged code so today's applies would have happened if inventory qualified.

## Counts
- Scanned: **3328** (morning: 3344)
- Qualifying: **0**
- Applied: **0** (none invented; none already applied today)
- Already: 0
- Failed/blocked (apply): 0
- External: 0
- Q answered: **0** | already-submitted: 0 | locked-empty: **0** | verify-empty: 0
- Awaiting listed: 0
- Failures (apply + locked-empty + verify-empty): **0**
- Tailored resumes: built **0** | profile uploaded **0** | upload failed 0

## Skip mix
ctc_under_35=1254, exp_max_low=1019, skip_title=774, location=234, no_tier_match=47

## Applied
_None_

## Failed applies
_None_

## Notes
- Auth OK (session cookie present; CDP :9222 + synced portal Chrome profile)
- Resume: `resumes/Rafi_Resume.docx` (rebuilt from `Mohammed_Abdul_Rafi_Ahmed_Resume.docx`)
- Questionnaire helper verified (`buildAnswerPayload` + non-empty check)
- Sampled `no_tier_match` titles are correct skips (Customer Success, Data Scientist, PHP/Symfony, Sales, UX/UI, ServiceNow, Tanium, MDM, Teamcenter, GenAI/Python) — not Architect / Tech Lead / EM / Senior .NET
- No new code-fixable blocker. Inventory still drained after prior applies.
- Artifact: `/opt/cursor/artifacts/` daily-run JSON (finishedAt=2026-08-30T14:42:29.417Z)
- Merged trigger PR: https://github.com/rafi-solibri/MyRepo/pull/293
