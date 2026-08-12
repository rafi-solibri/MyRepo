# Instahyre daily — 2026-08-12

Mohammed Abdul Rafi Ahmed | Expected **65 LPA** / Current **52 LPA** | Hyd + Remote | resume `Rafi_Resume.docx`

## Totals

| Metric | Count |
| --- | ---: |
| Applied (Instahyre in-app) | 3 |
| External ATS completed | 0 |
| Skipped | 677 |
| Blocked | 0 |

## Submitted

- **Intellect Design Arena** — Node.js Developer (Hyderabad) — path: Instahyre; UI: application_sent — [job 438112](https://www.instahyre.com/job-438112-node-js-developer-at-intellect-design-arena-hyderabad/)
- **Nineleaps** — Full - Stack Engineer (Bangalore,Hyderabad) — path: Instahyre; UI: application_sent — [job 438059](https://www.instahyre.com/job-438059-full-stack-engineer-at-nineleaps-2-bangalore-hyderabad/)
- **Uber** — Senior Staff Engineer (Hyderabad) — path: Instahyre; UI: application_sent — [job 437904](https://www.instahyre.com/job-437904-senior-staff-engineer-at-uber-hyderabad/)

## Code fix

- Branch: `cursor/instahyre-opportunities-feed-c8ce` (pushed)
- Problem: `daily_apply.js` only used `job_search`; recommended Hyd roles on undecided opportunities (e.g. Uber Senior Staff) were missed
- Fix: sweep `candidate_opportunity/?status=0` first
- PR: **not created** — `gh pr create` → Resource not accessible by integration; no ManagePullRequest tool in this environment

## Blockers

- None for login/CAPTCHA/apply API
- Owner/parent: open+merge PR from `cursor/instahyre-opportunities-feed-c8ce` into `main`

## Skip highlights (Hyd/remote, not already_interested)

Opportunities feed non-Hyd skips: Sigmoid Solutions Architect (Bangalore), Bupa Head of Engineering (Gurgaon), DTDL Director of Engineering (Gurgaon).

Artifact: `/opt/cursor/artifacts/instahyre-daily-run.json`
