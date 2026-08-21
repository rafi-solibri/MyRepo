# Hitech City / Knowledge City daily — 2026-08-21 (cloud cron 03:30 UTC)

## Totals
- **Submitted: 0** | Referrals: 0 | Blocked: 15 | Skipped: 65
- Report: `/opt/cursor/artifacts/hitechcity-daily.json`
- Mode: `OWNER_ASLEEP=1` (overnight)

## Phases
| Phase | Result |
| --- | --- |
| Discovery | 92 companies (0 added, 92 updated) |
| Careers parallel (10 tabs) | 0 applied / 11 blocked / 14 skipped / 93 scanned |
| LinkedIn + referrals | `linkedin_login_required` (Google SSO → CAPTCHA checkpoint) |
| Boards | Naukri timeout_900s; Foundit/Cutshort/Instahyre ok 0; Indeed timeout_900s |

## Careers blocked (sample)
- JPMorgan Chase ×3 — CAPTCHA/bot wall (Hyd .NET EM / Lead)
- Experian — CAPTCHA/bot wall (Director of Engineering Hyd)
- ModMed / Gartner ×2 — ats_login_wall
- Oracle ×4 — external_incomplete_or_timeout (ASK_OWNER 12s while asleep)

## Owner actions needed
1. LinkedIn headed login / CAPTCHA: `bash scripts/home-headed-login.sh linkedin` (restriction memory until 2026-08-23)
2. Solve career-portal CAPTCHAs when awake (JPMC Oracle Cloud, Experian SmartRecruiters)

## Code fix shipped same day
- Gartner `(Remote- US)` / `(Remote - U.S.)` + Workday `Remote---Texas` false-passed location filter
- Oracle Performance/Load Test titles burned soft incompletes — now CAREERS_TITLE_SKIP
