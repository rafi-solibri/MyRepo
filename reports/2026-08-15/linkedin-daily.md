# LinkedIn daily — 2026-08-15

## Status
**STOPPED — LinkedIn CAPTCHA/checkpoint** (owner-only). No applies.

Same-day post-fix re-run pulled `main` @ `ce373d6` (merged [PR #160](https://github.com/rafi-solibri/MyRepo/pull/160) ATS `tools/ats/complete.py`) and executed the daily job. Login still failed, so the ATS fix was **not exercised** on any company-site apply.

## Totals
- Easy Apply submitted: **0**
- External completed: **0**
- Skipped: **0**
- Blocked: **1** (login wall / security check)
- Dedup seed loaded: 92 prior job IDs (none newly scanned)
- Invented applies: **none**

## This post-fix re-run (PR #160)
- Agent: https://cursor.com/agents/bc-2ac79f3e-7136-47a5-bdbd-7515ed5cd0c2
- Preflight: resume + cookie sync OK (`destHasAuth` SQLite `li_at` name present)
- Live CDP primary (`chrome-cdp-profile`): stale session → `/uas/login`
- Auto-login: Google session present; Continue with Google **clicked: true**; password fallback then `/checkpoint/challenge` (reCAPTCHA “Let’s do a quick security check”)
- Auto-login exit **6**; launch `CDP_REQUIRE_LIVE_LOGIN=1` exit **5**
- Alt CDP profile also had SQLite `li_at` + live `/uas/login` (stale). Did not re-burn it with password login.
- Helpers ran with merged code and exited 5 (`BLOCKED: not signed in` for Easy Apply and external ATS).
- No new code fix / no additional same-day re-run (CAPTCHA is owner-only; re-run cap 2/5 used). Password-after-GSI CAPTCHA is the same wall as earlier today, not a new code-fixable blocker.

## Earlier same-day runs
| Run | Agent | Outcome |
| --- | --- | --- |
| Cron | `bc-0d1894c6` | 0 applies; merged **PR #157** (welcome-back Google SSO) |
| Post-fix #157 | `bc-c088e7fb` | 0 applies; GSI clicked; still CAPTCHA |
| Manual full | `bc-45718255` | 0 applies; same CAPTCHA; no PR |
| Post-fix #160 (this) | `bc-2ac79f3e` | 0 applies; GSI clicked; still CAPTCHA |

## Owner action
CAPTCHA with Google session present — not a missing Google SSO setup.

1. `bash scripts/home-headed-login.sh [REDACTED]` (complete Security Verification on the CDP profile)
2. Confirm feed loads with a **live** `li_at`
3. `bash scripts/refresh-portal-session-seed.sh [REDACTED]` and Save snapshot

## Artifacts
- `/opt/cursor/artifacts/apply-report.json`
- `/opt/cursor/artifacts/daily-apply-report.json`
- `/opt/cursor/artifacts/external-apply-report.json`
- `/opt/cursor/artifacts/*-daily-run.json` and checkpoint screenshots
- Resume: `resumes/Rafi_Resume.docx`
