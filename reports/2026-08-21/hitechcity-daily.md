# Hitech City / Knowledge City daily — 2026-08-21

## Morning cron (03:30 UTC, `OWNER_ASLEEP=1`)
- **Submitted: 0** | Referrals: 0 | Blocked: 15 | Skipped: 65
- LinkedIn: `linkedin_login_required` (Google SSO → CAPTCHA)
- Boards: Naukri/Indeed timeout; others 0
- Code fix shipped same day in [#230](https://github.com/rafi-solibri/MyRepo/pull/230): Gartner `(Remote- US)` / `(Remote - U.S.)` + Workday `Remote---Texas`; Oracle Performance/Load Test titles → `CAREERS_TITLE_SKIP`

## Post-fix re-run (04:26–04:37 UTC, careers-only)
Ran on **main @ `3fe31e2`** (merged #230). Company career portals first, 10 parallel tabs, no LinkedIn CAPTCHA wait.

### Totals
- **Submitted: 0** (confirmation text only — none found; no invented applies)
- Referrals: 0 (LinkedIn phase skipped)
- Blocked: 10 | Skipped: 14 | Scanned: 92
- Discovery: 92 companies (0 added)
- Report: `/opt/cursor/artifacts/[REDACTED]-daily.json`
- Chat log: `/opt/cursor/artifacts/[REDACTED]-apply-chat.jsonl`

### Phases
| Phase | Result |
| --- | --- |
| Discovery | 92 companies (0 added, 92 updated) |
| Careers parallel (10 tabs) | 0 applied / 10 blocked / 14 skipped / 92 scanned |
| LinkedIn + referrals | skipped (careers-only) |
| Boards | skipped (careers-only) |

### #230 fix observed
- Gartner `(Remote- US)` / Workday `Remote---Texas` were **not** opened
- Oracle Performance/Load Test titles were **not** opened
- Remaining Oracle Hyd roles were real matching titles (Forward Deployed / Core Infrastructure)

### Careers attempted (not submitted)
| Company | Role | Campus | Reason |
| --- | --- | --- | --- |
| JPMorgan Chase | Lead Software Engineer Hyderabad (×2) | Knowledge City / Mindspace | CAPTCHA/bot wall |
| JPMorgan Chase | Senior Director of Software Engineering — Data Governance / AWS Hyderabad | Knowledge City / Mindspace | CAPTCHA/bot wall |
| Experian | Lead Software Engineer - Mainframe Hyderabad | Mindspace / Cyber Pearl | CAPTCHA/bot wall |
| Experian | Director of Engineering Hyderabad | Mindspace / Cyber Pearl | CAPTCHA/bot wall |
| Experian | Senior Staff Software Engineer Hyderabad | Mindspace / Cyber Pearl | CAPTCHA/bot wall |
| ModMed | Senior Software Architect · Hyderabad | Mindspace / Cyber Pearl | ats_login_wall |
| Oracle | Senior Principal Forward Deployed Engineer HYDERABAD | Knowledge City | external_incomplete_or_timeout (`/apply/email`) |
| Oracle | Principal Core Infrastructure Engineer HYDERABAD (×2) | Knowledge City | external_incomplete_or_timeout (`/apply/email`) |

### Skips (host / location, not invented)
- Intel, Solera — `workday_no_hyderabad_facet`
- Apple, Goldman Sachs, Meta — `hang_scan_host`
- Optum / UHG — `skip_uhg`

### Owner actions (not code-fixable)
1. Headed login / CAPTCHA: `bash scripts/home-headed-login.sh linkedin` (restriction memory until 2026-08-23)
2. Solve career CAPTCHAs when awake: JPMC Oracle Cloud, Experian SmartRecruiters
3. Oracle `/apply/email` forms stay open after persist_retry — finish in headed Chrome (`ASK_OWNER`)
4. ModMed Workday Sign In

No **new** code-fixable blocker. Remaining walls are CAPTCHA / login / owner form finish. Post-fix re-run count for this portal today: **1 / 5**.
