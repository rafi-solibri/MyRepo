# Daily apply 2026-08-23 — portal 03 post-fix re-run

## Post-fix re-run (POST_FIX_RERUN=1)

Same-day re-run on merged `main` after https://github.com/rafi-solibri/MyRepo/pull/244
(`chore(resume): use Mohammed_Abdul_Rafi_Ahmed_Resume as master base`).

- HEAD: `df7b068`
- Source: `post-fix-rerun`
- Finished: 2026-08-23T15:11:13.931Z
- Auth: OK (candidate dashboard live)
- Resume: `/workspace/resumes/Rafi_Resume.docx` (3,689,045 bytes — merged master, not the 17KB stub used by the 03:37 UTC cron)
- Runner: `node tools/<portal>/daily_apply.js` exit 0
- Already-applied today: none (morning cron also Applied **0**)
- New code-fixable blocker: **none** — did not launch another re-run (cap 5)

Morning cron (`bc-464ebdea-b53b-4bec-865a-da68420c6ffe`) scanned 3296 / qualifying 0 before this fix landed. This re-run executed the apply path with the merged resume so today's inventory was not skipped.

## Counts
- Scanned: **3282**
- Qualifying: **0**
- Applied: **0**
- Already: 0
- Failed/blocked (apply): 0
- External: 0
- Q answered: **0** | already-submitted: 0 | locked-empty: **0** | verify-empty: 0
- Awaiting listed: 0
- Failures (apply + locked-empty + verify-empty): **0**
- Tailored resumes: built **0** | profile uploaded **0** | upload failed 0

## Filter skips
- `ctc_under_35`: 1211
- `exp_max_low`: 1029
- `skip_title`: 772
- `location`: 226
- `no_tier_match`: 44

Inventory still drained (same pattern as 2026-08-21 / 2026-08-22 / morning 2026-08-23). No invented applies.

## Applied
_None_

## Failed applies
_None_

## Artifacts
- `/opt/cursor/artifacts` daily-run JSON (source=post-fix-rerun)
- `/tmp` daily_apply.log + stats.json
