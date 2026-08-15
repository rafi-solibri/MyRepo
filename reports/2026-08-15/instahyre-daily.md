# Daily apply — 2026-08-15 (post-fix re-run after #164)

Mohammed Abdul Rafi Ahmed | Expected **65 LPA** / Current **52 LPA** | Hyd + Remote | resume `Rafi_Resume.docx`

**POST_FIX_RERUN=1** on merged `586c376` (`fix(ats): fail-fast brochure pages and false Apply CTAs so external applies complete (#164)`).

Earlier same-day runs (original daily + post-fix #1–#4) executed **before** #164 and recorded **0** applies. This job pulled `origin/main` and ran the durable `daily_apply.js` helper with the merged completer.

## Totals

| Metric | Count |
| --- | ---: |
| Applied (in-app) | 0 |
| External ATS completed | 0 |
| Skipped | 677 |
| Blocked | 0 |
| Unique jobs seen | 677 |
| Undecided opportunities swept | 3 |
| Interested (before → after) | 449 → 449 |

No invented applies. Eligible Hyd/remote Architect / Tech Lead / EM / Principal / Staff / Senior .NET roles in inventory are already `already_interested` (73 Hyd/WFH of 89). The ATS completer from #164 only follows company-site links on **new** in-app submits this run, so it was not invoked.

## Submitted

None.

## Login / preflight

- `bash scripts/preflight-portal-run.sh` — OK (`sessionid` present)
- resume helper — `/workspace/resumes/Rafi_Resume.docx`
- Chrome CDP :9222
- Live CDP: logged in on `/candidate/opportunities/?matching=true`

## Undecided opportunities (all location-skipped)

1. Sigmoid — Solutions Architect (Bangalore)
2. Bupa — Head of Engineering (Gurgaon)
3. Deutsche Telekom Digital Labs — Director of Engineering (Full Stack) (Gurgaon)

## Top skip reasons

- location_not_hyd_remote: 551
- already_interested: 89
- generic_engineering_without_dotnet_cloud: 24 (React/Python/Java IC, no seniority)
- pure_ai_data_without_dotnet: 6 (Azure/AWS Data Engineer titles)
- java_primary: 4
- frontend_without_dotnet: 1
- qa_quality_engineering: 1
- wrong_stack_title: 1 (ServiceNow Technical Architect)

Remaining Hyd/WFH non-interested titles were title-first skips (not SA/TL/EM/Staff/.NET).

## Blockers

None (login, CAPTCHA, apply API, resume path). `rateLimited: 1` during job_search; helper backed off and continued.

## Auto-fix

No **new** code-fixable blocker. Did not launch another post-fix re-run (this is re-run #6 of 10 for this portal on 2026-08-15 IST).

Artifact: `/opt/cursor/artifacts/` apply-report + daily-run JSON
