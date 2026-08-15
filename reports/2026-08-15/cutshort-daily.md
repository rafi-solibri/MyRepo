# Cutshort daily 2026-08-15 (post-fix re-run) <!-- pragma: allowlist secret -->

**POST_FIX_RERUN=1** on `main` @ `92bb3cc` (ATS PR #161) plus same-session inventory fix `c9a0fe9` (`pageSize=50` + senior `expMax>=6`).

Login: OK (candidate dashboard, live CDP). Resume: `/workspace/resumes/Rafi_Resume.docx`.

## Counts (this re-run)
- Scanned: **3214** (unfixed `main` only saw ~1190 @ pageSize=5)
- Qualifying: **0**
- Applied: **0** (none invented)
- Already (this pass): 0 — the 3 jobs applied earlier today are gone from `/findjobs`
- Failed/blocked (apply): 0
- External: 0
- Q answered: **0** | already-submitted: 33 | locked-empty: **323** (historical, not same-day apply failures) | verify-empty: 0
- Awaiting listed: 359
- Failures (apply + locked-empty + verify-empty): **323**

Skip taxonomy: location 212 · no_tier_match 56 · skip_title 759 · ctc_under_35 1167 · exp_max_low 1020

## Already applied earlier today (skip — do not re-apply)
From the original morning daily 2026-08-15 second pass (local pageSize fix, PR never merged):

| ID | Title | Company | Via |
|----|-------|---------|-----|
| `6a1fd51dd7bf645877d57db8` | Principal Engineer, Salesforce Health Cloud | Unique Occupational (38L, T1) | `api_no_ui_button` |
| `6a4b58ed80b936a4374760b4` | Senior Full-Stack Engineer | Recro (38L, T2) | `api_no_ui_button` |
| `6a2146d3654875adb93e1546` | Sr. AI Ops Engineer | Fx31labs (45L, T3) | `api_no_ui_button` |

## Applied this re-run
_None_ — remaining public inventory has no new Hyd/remote Architect / Tech Lead / EM / Principal / Staff / Senior .NET cards at ≥35L.

## Near-misses inspected (56 `no_tier_match`) — not applied
Wrong-fit / title-first skips (not invented as applies): Customer Success, Product Marketing, UX/UI, Ontologist, PHP/Symfony, Salesforce ServiceMax, Oracle MDM/OIC, ServiceNow, IT Support Director, Pre-Sales Solutions Engineer, pure data/ML titles (Senior Data Scientist, Data Platform Lead, Enterprise Data Modeller), sales Regional Partner.

Stretch but still skipped (not Architect/Tech Lead/.NET): POD Lead (ML pod), AWS Cloud Engineer (Hyd IC 35L), Frontend Engineer (React remote), Cloud AI Engineer, Copilot/M365 developer.

## Failed applies
_None_

## Code fix (this re-run)
`pageSize=5` was a **new** code-fixable blocker on `main` even after ATS #161: 120 newest pages never reached the ~3200 inventory. Feature branch @ `c9a0fe9` pushed. `gh pr create` returned **403 Resource not accessible by integration** (same as the morning daily). Filter tests: `node tools/*/test_filters.js` OK.

Artifacts: `/opt/cursor/artifacts/*-daily-run.json`, `/tmp/*-run/stats.json`
