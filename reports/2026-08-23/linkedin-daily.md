# LinkedIn daily — 2026-08-23

## Status
**HANDED OFF** to same-day post-fix re-run after code fix merge. This session did **not** invent applies.

## Login
- Preflight OK (`li_at` present in source + CDP profile)
- Temporary restriction lift `2026-08-23T03:30:00+00:00` matched cron; auto-login waited ~90s then Google SSO → feed
- Live CDP check OK; seed refresh initially raced (pre-flush), then succeeded after wait
- Screenshot from restriction wait: `/opt/cursor/artifacts/linkedin-auto-login-captcha.png`

## This session totals (before handoff)
| Path | Count |
| --- | --- |
| Easy Apply submitted | **0** (confirmed) |
| External / ATS completed | **0** (not started; handoff) |
| Skipped (search pass) | many — Sitecore, SAP/ABAP, Salesforce Developer, Data Scientist, EDA AI/ML, APAC location, already-applied |
| Blocked / hung | 1 mid-form before kill (bait-and-switch job `4453425544`) |

## Notable false-apply / parse bug (fixed)
- Search card text: “Laureate, Software Engineer - .NET Architecture”
- Canonical `/jobs/view/4453425544/`: **Azure Data Engineer** @ Strive4X Infotech (Chennai | Bengaluru | Hyderabad)
- Cause: page-wide `a[href*='/jobs/view/'].first` + company link matched the **left list**, not the open top-card
- Easy Apply modal opened; fill loop hung past effective time-cap (ep_poll) → process killed

## Code fix
- PR: https://github.com/rafi-solibri/MyRepo/pull/238 (merged)
- Scope top-card parse; re-validate location / `skip_reason` / `TITLE_OK` on `/jobs/view` before Easy Apply
- `fill_inputs` deadline + `body.inner_text` timeout; seed cookie wait/retry after SSO
- Issues log: `automation-prompts/issues/linkedin.md`

## Same-day re-run
- https://cursor.com/agents/bc-902b0e1a-8586-4ff5-9a72-c4c34e6e1199
- This session **stopped applying** so the new job owns inventory with the merged fix

## Artifacts
- `/opt/cursor/artifacts/linkedin-easy-apply.log`
- `/opt/cursor/artifacts/search-*.png`
- `.portal-sessions` Cookies refreshed (Local State omitted from commit)
