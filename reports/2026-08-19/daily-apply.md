# Daily apply — 2026-08-19 (cloud)

Mohammed Abdul Rafi Ahmed | Expected **65 LPA** / Current **52 LPA** | Hyd + Remote | resume `Rafi_Resume.docx`

Logged in via CDP (`sessionid` live on `/candidate/opportunities/`). No invented applies — in-app `apply` API + interested counts.

## Totals

| Metric | First pass | After filter fix |
| --- | ---: | ---: |
| Applied (in-app) | 1 | +1 |
| External ATS completed | 0 | 0 |
| Skipped | 670 | 671 |
| Blocked | 0 | 0 |
| Interested count | 436 → 437 | 437 → 438 |

## Submitted

- **DAT Freight & Analytics** — SDE - 3 (Work From Home) — path: in-app; UI: application_sent — job 423301 / opp 6184011665
- **Amazon** — Sr. Software Engineer (Hyderabad) — path: in-app; UI: application_sent — job 439255 / opp 6184030768 *(second pass after filter fix)*

## Code fix

- `hasTargetSeniority` now includes `senior` / `sr.` so Hyd/remote senior SWE is apply-bias (uncertain → APPLY). Java-primary / QA / AI-data title skips still win first.
- `enqueueJob` passes `title` + `skills` into `locationOk` (pan-India senior soften).
- Tests: `node tools/*/filters.location.test.js`
- Artifact (first): `/opt/cursor/artifacts/*-apply-report.json`
- Artifact (re-run): `/opt/cursor/artifacts/*-apply-report-rerun.json`

## Blockers

- None (login / CAPTCHA / apply API). Company-site ATS not opened (in-app application_sent; no external apply links on the two submitted jobs).

## Skip highlights

Undecided opportunities (all non-Hyd): Sigmoid Solutions Architect (Bangalore); Bupa Head of Engineering (Gurgaon); DTDL Director of Engineering (Gurgaon).

Remaining Hyd/remote senior skips after fix: EPAM Senior Java Full Stack (java_primary); Visionet ServiceNow Technical Architect (wrong_stack_title).

Top skip reasons (re-run): location_not_hyd_remote 551; already_interested 85; generic_engineering_without_dotnet_cloud 23.
