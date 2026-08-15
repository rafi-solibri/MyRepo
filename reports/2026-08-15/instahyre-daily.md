# Daily apply — 2026-08-15 (post-fix re-run after #169)

Mohammed Abdul Rafi Ahmed | Expected **65 LPA** / Current **52 LPA** | Hyd + Remote | resume `Rafi_Resume.docx`

**POST_FIX_RERUN=1** on merged `02e58e4` (`fix(hitechcity): complete Workday/guest career applies instead of walling JD chrome (#169)`).

This job fetched `origin/main`, checked it out, and ran the durable helper so today's apply path used the merged code. Earlier same-day runs finished **before** #169 and also recorded **0** applies (eligible inventory already `already_interested`).

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

No invented applies. Eligible Hyd/remote Architect / Tech Lead / EM / Principal / Staff / Senior .NET roles in inventory are already `already_interested` (74 Hyd/WFH of 90). Remaining Hyd/WFH listings were title-first skips. The company-site completer only follows ATS links on **new** in-app submits this run, so it was not invoked.

## Submitted

None.

## Login / preflight

- preflight script — OK (session cookie present)
- resume helper — `/workspace/resumes/Rafi_Resume.docx`
- Chrome CDP :9222
- Live CDP: logged in on `/candidate/opportunities/?matching=true` (Hey Rafi)

## Undecided opportunities (all location-skipped)

1. Sigmoid — Solutions Architect (Bangalore)
2. Bupa — Head of Engineering (Gurgaon)
3. Deutsche Telekom Digital Labs — Director of Engineering (Full Stack) (Gurgaon)

## Top skip reasons

- location_not_hyd_remote: 550
- already_interested: 90
- generic_engineering_without_dotnet_cloud: 24 (React/Python/Java IC, no seniority)
- pure_ai_data_without_dotnet: 6 (Azure/AWS Data Engineer titles)
- java_primary: 4
- frontend_without_dotnet: 1
- qa_quality_engineering: 1
- wrong_stack_title: 1 (ServiceNow Technical Architect)

## Blockers

None (login, CAPTCHA, apply API, resume path). `rateLimited: 1` during job_search; helper backed off and continued.

## Auto-fix

No **new** code-fixable blocker. Did not launch another post-fix re-run (this is a same-day re-run after #169; cap is 20 for this portal on 2026-08-15 IST).

Artifact: `/opt/cursor/artifacts/` apply-report + daily-run JSON
