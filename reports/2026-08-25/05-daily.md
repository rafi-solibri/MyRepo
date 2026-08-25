# Portal 05 daily — 2026-08-25 (post-fix re-run)

`POST_FIX_RERUN=1` on merged `main` after [#257](https://github.com/rafi-solibri/MyRepo/pull/257) / [#259](https://github.com/rafi-solibri/MyRepo/pull/259) (hirist DESTS alignment in `sync-chrome-sessions.sh`). Resume: `resumes/Rafi_Resume.docx`.

## Status
**Completed.** Logged in. **0** new applies this session (none invented). Earlier same-day applies were skipped as already interested.

## Preflight / login
- `bash scripts/preflight-portal-run.sh` for portal 05 — **ok** (`destHasAuth` + session cookie)
- Resume helper — `/workspace/resumes/Rafi_Resume.docx` (3,957,700 bytes)
- Chrome CDP :9222 with the synced portal 05 profile
- Live session: opportunities dashboard (interested=455, undecided=6)

## Totals (this re-run)

| Metric | Count |
| --- | ---: |
| Applied (in-app) | **0** |
| Company ATS completed | **0** (no new in-app applies to follow) |
| Skipped | **676** |
| Blocked | **0** |
| Unique jobs seen | 676 |
| Undecided opportunities | 6 (all non-Hyd/non-remote) |

`countsBefore` = `countsAfter` = interested 455 / undecided 6 / rejected 28.

## Already applied today (skipped, not re-applied)
1. **Vortiqo Technologies** — Lead Solution Architect - AWS (Work From Home) — job 440001
2. **HighLevel** — SDE 3 (Social Planner) (Work From Home) — job 439867

## Skip reasons
- location_not_hyd_remote: 545
- already_interested: 93
- generic_engineering_without_dotnet_cloud: 21
- java_primary: 8
- pure_ai_data_without_dotnet: 6
- frontend_without_dotnet: 1
- qa_quality_engineering: 1
- wrong_stack_title: 1

## Undecided feed (all location-skipped)
Mercari EM (Bangalore), Sigmoid Solutions Architect (Bangalore), Bupa Head of Engineering (Gurgaon), Nexthink EM (Bangalore), Alora Advisors Senior EM - AI Product (Chennai), DTDL Director of Engineering (Gurgaon).

## Blockers
None. No new code-fixable issue. No further post-fix re-run launched (this is re-run 1 of 5 for 2026-08-25).

Artifact: `/opt/cursor/artifacts` apply-report JSON from this session.
