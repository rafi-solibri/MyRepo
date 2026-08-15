# Instahyre daily — 2026-08-15 (post-fix re-run #5 / 5)

Mohammed Abdul Rafi Ahmed | Expected **65 LPA** / Current **52 LPA** | Hyd + Remote | resume `Rafi_Resume.docx`

Ran on `main` @ `586c376` after merged [PR #164](https://github.com/rafi-solibri/MyRepo/pull/164) (ATS brochure / false Apply CTA fail-fast). Earlier same-day Instahyre runs did not apply with this fix. This job executed `daily_apply.js` with the merged code.

## Totals

| Metric | Count |
| --- | ---: |
| Applied (Instahyre in-app) | 0 |
| External ATS completed | 0 |
| Skipped | 677 |
| Blocked | 0 |
| Unique jobs seen | 677 |
| Undecided opportunities | 3 |
| Interested (before → after) | 449 → 449 |

## Submitted

None. Do not invent applies. No jobs were submitted today (in-app or company ATS).

## Why 0 applies

Eligible Hyd/remote senior / .NET / architect / EM inventory is already `already_interested` from 2026-08-11–14 (73 Hyd/WFH of 89 already-interested). Remaining Hyd/WFH listings are title-first skips (data/AI, generic IC without .NET/cloud, Java-primary, frontend, QA, ServiceNow). The 3 undecided feed jobs are non-Hyd (Bangalore / Gurgaon).

PR #164’s company-site completer was on the runner but never invoked: `complete_page.js` only follows ATS hrefs after a **new** in-app submit, and there were none.

## Top skip reasons

- location_not_hyd_remote: 551
- already_interested: 89
- generic_engineering_without_dotnet_cloud: 24
- pure_ai_data_without_dotnet: 6
- java_primary: 4
- frontend_without_dotnet / qa_quality_engineering / wrong_stack_title: 1 each

## Hyd/WFH title-first skips (not already interested)

Data Engineer titles (Two Circles, Insight, Amazon, Coforge, KPMG, Nihilent); React / React Native / Python / Java ICs; Front End Developer - Angular; SDET - Java; ServiceNow Technical Architect. Filters match the prompt (title-first; do not skip because JD casually mentions adjacent tech).

## Already-interested Hyd/WFH highlights (skipped; not re-applied)

Sonata Dotnet Architect; American Airlines Principal Engineer; Qapita Engineering Manager; DataArt Senior .NET; Hevinsoft Senior Full-Stack ASP.NET; Axi App Development Architect; plus prior .NET IC roles (Cognizant, Improving, EverestEngineering, Anblicks, etc.).

## Blockers

None (login/CDP/CAPTCHA/apply API). `rateLimited: 1` during search; recovered. Filter self-check: QE skip, Staff .NET allow, AI Architect skip.

## Auto-fix

No **new** code-fixable blocker. Same-day post-fix re-run cap is **5 / 5** for this portal — did not launch another re-run.

## Artifact

`/opt/cursor/artifacts/instahyre-apply-report.json`
