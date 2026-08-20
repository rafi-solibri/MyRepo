# Hitech City / Knowledge City daily — 2026-08-20 (post-fix re-run, careers-only)

## Status
**Careers-only completed on merged PR #218** (`4179d58`, Hyd-title false-skip fix).
**Confirmation applies: 0.** Do not invent counts. LinkedIn + boards skipped (careers-only).

`CAREERS PARALLEL start tabs=10` — 60 companies, 10 workers.

## Applied (confirmation text)
None. No ATS “application submitted” / “currently submitted” banners this run.

## Opened matching Hyd roles (not submitted)
- **Oracle** — Senior Principal Forward Deployed Engineer HYDERABAD (PR #218 unblocked this title; previously `location_non_hyd_city`)
- **Oracle** — Principal Core Infrastructure Engineer HYDERABAD (×2)
- **JPMorgan Chase** — Manager of Software Engineering - .Net, C# Hyderabad
- **JPMorgan Chase** — Lead Software Engineer Hyderabad (×2)
- **ModMed** — Senior Software Architect · Hyderabad, India
- **Experian** — Director of Engineering · Hyderabad, India

## Blocked (10)
| Company | Role | Reason |
| --- | --- | --- |
| JPMorgan Chase | Manager of Software Engineering - .Net, C# Hyderabad | CAPTCHA/bot wall |
| JPMorgan Chase | Lead Software Engineer Hyderabad | CAPTCHA/bot wall |
| JPMorgan Chase | Lead Software Engineer Hyderabad | CAPTCHA/bot wall |
| ModMed | Senior Software Architect · Hyderabad, India | ats_login_wall |
| Gartner | Sr Director Analyst, AI and Software Engineering (Remote- US) | ats_login_wall (should not have opened) |
| Gartner | Senior Director Analyst - Software Engineering for AI and Agentic Applications | ats_login_wall |
| Experian | Director of Engineering · Hyderabad, India | CAPTCHA/bot wall |
| Oracle | Senior Principal Forward Deployed Engineer HYDERABAD | external_incomplete_or_timeout (email OTP after AGREE+NEXT) |
| Oracle | Principal Core Infrastructure Engineer HYDERABAD | external_incomplete_or_timeout |
| Oracle | Principal Core Infrastructure Engineer HYDERABAD | external_incomplete_or_timeout |

## Skipped
- Optum / UnitedHealth Group — `skip_uhg`
- Intel / Solera — `workday_no_hyderabad_facet`
- Apple / Goldman Sachs / Meta — `hang_scan_host`
- Many catalog tenants — empty `careersUrls` (LinkedIn-only; not this careers-only pass)

## New code fix (same day)
Oracle `/apply/email` Close overlay stole Next; after AGREE+NEXT the form requires an emailed OTP (`Confirm Your Identity`). Follow-up branch fails-fast that wall, skips Close/honeypot/chat file inputs, and skips `Remote- US` titles.

## Artifacts
- `/opt/cursor/artifacts/*-daily.json` — applied 0, blocked 10, skipped 14
- `/opt/cursor/artifacts/*-careers.json`
- `/opt/cursor/artifacts/*-apply-chat.jsonl`
- `/opt/cursor/artifacts/*-discovery.json` — 92 tenants, 0 added
