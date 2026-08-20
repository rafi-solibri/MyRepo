# Hitech City / Knowledge City daily — 2026-08-20 (post-fix re-run, careers-only)

## Status
**Careers-only completed on merged PR #218** (`4179d58`, Hyd-title false-skip fix), then the same session re-ran with Oracle email-OTP fail-fast (`66b57aa`).
**Confirmation applies: 0.** Do not invent counts. LinkedIn + boards skipped (careers-only).

`CAREERS PARALLEL start tabs=10` — 60 companies, 10 workers.

## Applied (confirmation text)
None. No ATS “application submitted” / “currently submitted” banners this run.

## Opened matching Hyd roles (not submitted)
- **Oracle** — Senior Principal Forward Deployed Engineer HYDERABAD (PR #218 unblocked this title)
- **Oracle** — Principal Core Infrastructure Engineer HYDERABAD
- **JPMorgan Chase** — Manager of Software Engineering - .Net, C# Hyderabad
- **JPMorgan Chase** — Lead Software Engineer Hyderabad
- **ModMed** — Senior Software Architect · Hyderabad, India
- **Experian** — Director of Engineering · Hyderabad, India

## Blocked (final OTP-fail-fast pass)
| Company | Role | Reason |
| --- | --- | --- |
| JPMorgan Chase | Manager of Software Engineering - .Net, C# Hyderabad | CAPTCHA/bot wall |
| JPMorgan Chase | Lead Software Engineer Hyderabad | CAPTCHA/bot wall |
| ModMed | Senior Software Architect · Hyderabad, India | ats_login_wall |
| Gartner | Senior Director Analyst - Software Engineering for AI and Agentic Applications | ats_login_wall |
| Experian | Director of Engineering · Hyderabad, India | CAPTCHA/bot wall |
| Oracle | Senior Principal Forward Deployed Engineer HYDERABAD | ats_login_wall (email OTP) |
| Oracle | Principal Core Infrastructure Engineer HYDERABAD | ats_login_wall (email OTP) |

Salesforce was reached after Oracle wall-capped (previously starved). HighRadius / Chubb / Macquarie / Persistent have empty `careersUrls`.

## Skipped
- Optum / UnitedHealth Group — `skip_uhg`
- Intel / Solera — `workday_no_hyderabad_facet`
- Apple / Goldman Sachs / Meta — `hang_scan_host`

## Code fix (same day, branch pushed)
Oracle `/apply/email`: Playwright Close overlay stole Next; Jet AGREE needs a DOM click; after Next the form sends an emailed OTP (`Confirm Your Identity`). Fail-fast as login wall; skip chat/honeypot file inputs; skip `Remote- US` titles.

PR create from this agent was blocked (`Resource not accessible by integration` / user-approval). Branch: `cursor/hitech-city-knowledge-city-daily-post-fix-re-run-2026-08-20-3913`.

## Artifacts
- `/opt/cursor/artifacts/*-daily.json` — applied 0, blocked 9, skipped 14
- `/opt/cursor/artifacts/*-careers.json`
- `/opt/cursor/artifacts/*-apply-chat.jsonl`
