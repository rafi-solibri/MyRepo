# Daily apply — 2026-08-18 (same-day post-fix re-run)

`POST_FIX_RERUN=1` on merged `main` (`46012f5`, includes `fix(ats): import os in persist_retry path` #208).
Earlier 2026-08-18 cron did not apply with that fix. This session executed `tools/*/daily_apply.js` after portal preflight + Chrome CDP.

Mohammed Abdul Rafi Ahmed | Expected **65 LPA** / Current **52 LPA** | Hyd + Remote | resume `Rafi_Resume.docx`

## Totals

| Metric | Count |
| --- | ---: |
| Applied (in-app) | 2 |
| External ATS completed | 0 |
| Skipped | 674 |
| Blocked | 0 |
| Unique jobs seen | 676 |
| Interested (API counts) | 449 → 451 |
| Opportunity total | 480 → 482 |

Logged in: **yes**. Resume: `/workspace/resumes/Rafi_Resume.docx`. searchErrors: 0.

## Submitted

- **Snap** — Azure / .NET Developer (Gurgaon,Hyderabad,Mumbai) — path: in-app; UI: application_sent — opp `6181103110` — job 438811
- **D. E. Shaw** — Backend Engineer (Bangalore,Gurgaon,Hyderabad) — path: in-app; UI: application_sent — opp `6181103114` — job 438809

Both `appliedOn` 2026-08-18T05:31:38–39Z. Not invented. No company-site ATS href after spot-check (`application_sent` only).

## Skipped (not invented)

- already_interested: 83 (69 Hyd/WFH already expressed — skipped)
- location_not_hyd_remote: 554, including undecided opportunities: Sigmoid SA (Bangalore), Bupa Head of Engineering (Gurgaon), DTDL Director of Engineering (Gurgaon)
- Hard title skips on remaining Hyd/WFH opens: Data Engineer (no .NET on title), Java IC, React/Python/Full Stack IC without .NET/cloud, SDET, ServiceNow Technical Architect

## Blocked

None (login, CAPTCHA, apply API, CDP). No new code-fixable helper bug this run. Did not launch another post-fix re-run.

Artifact: `/opt/cursor/artifacts/*-apply-report.json`
