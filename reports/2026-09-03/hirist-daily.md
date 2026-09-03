# Hirist Daily post-fix re-run — 2026-09-03 IST

POST_FIX_RERUN=1 after merged [#315](https://github.com/rafi-solibri/MyRepo/pull/315) (`fix(hirist): HARD-skip E2Open/GTM product titles`).
Ran on `origin/main` @ `4e462d9`. Resume: `/workspace/resumes/Rafi_Resume.docx`. Login: `login_ok` at `/jobfeed`.

## Corrected counts (this re-run)

| applied | external | rejected | blocked | skipped | seen |
| --- | --- | --- | --- | --- | --- |
| **0** | 0 | 0 | 0 | 447 | 447 |

Do **not** invent applies. The runner first reported 2 in-app applies; both were `apply-multiple` HTTP 200 with `success: false` (`Assessment/ screening is required`). Hirist applied-jobs count stayed **196** / `lastAppliedJobId=1661575`. Those two are skipped as `assessment_required`, not applied.

## #315 filter check

- **E2Open GTM Architect** (ARA Resources, `1668034`) → `wrong_stack_title` (not re-applied).

## Morning run (before this re-run) — corrected

Earlier agent counted 6 applies. Applied-jobs + apply-multiple probe:

| id | title | company | Real? |
| --- | --- | --- | --- |
| 1661575 | Full Stack Developer - .Net/Azure | MOURI Tech | yes (Applied on JD) |
| 1668077 | .Net Azure Engineer - Microservices Architecture | Volto Consulting | yes |
| 1661418 | Senior .Net Full Stack Developer | MOURI Tech | yes |
| 1668034 | E2Open GTM Architect | ARA Resources | **no** — filter miss; now skipped |
| 1667999 | Full Stack Developer - .Net/AngularJS | DIgitalcubez | **no** — assessment required |
| 1667966 | Full Stack Developer - .Net Core & AngularJS | Workplace | **no** — assessment required |

This re-run did not re-POST the three real morning applies (they are on `/job/applied-jobs`). It did POST the two assessment jobs again because search still listed them and HTTP 200 was treated as success — that is the new helper bug below.

## New code-fixable blocker (this re-run)

`POST /job/apply-multiple` returns HTTP 200 with `[{ success: false, message: { message: "…" } }]`. `daily_apply.js` treated “200 and no `.error`” as applied.

Fix in this branch:

- Parse the array via `tools/hirist/apply_response.js`
- Skip IDs already on `GET /job/applied-jobs?page=&status=`
- Skip `already_applied` / `assessment_required` (not counted as apply)

## Top skip reasons (this scan)

- 264× location_not_hyd_remote
- 68× pure_ai_data_without_dotnet
- 37× wrong_stack_title (includes E2Open/GTM)
- 32× java_primary
- 21× generic_engineering_without_dotnet_cloud
- 2× assessment_required (Digitalcubez, Workplace)

## In-session verify (after parser fix)

Re-ran `node tools/hirist/daily_apply.js` on this pod (could not auto-merge/launch another cloud agent — `gh pr create` is integration-blocked).

| applied | external | rejected | blocked | skipped | seen | applied-jobs IDs |
| --- | --- | --- | --- | --- | --- | --- |
| **0** | 0 | 0 | 0 | 445 | 445 | 248 |

Confirmed skips:

- DIgitalcubez `1667999` → `assessment_required`
- Workplace `1667966` → `assessment_required`
- E2Open GTM Architect `1668034` → `wrong_stack_title`
- Talkdesk Solution Architect `1662739` → `already_applied`

No remaining eligible in-app candidates without assessment.

## Artifacts

- `/opt/cursor/artifacts/hirist-apply-report.json`
- `/opt/cursor/artifacts/hirist-daily-run.json`
- `reports/2026-09-03/hirist-apply-report.json`
