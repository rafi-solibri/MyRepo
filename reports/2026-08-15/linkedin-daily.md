# LinkedIn daily — 2026-08-15

## Status
**STOPPED — LinkedIn CAPTCHA/checkpoint** (owner-only). No applies.

## Totals
- Easy Apply submitted: **0**
- External completed: **0**
- Skipped: **0**
- Blocked: login wall / security check

## Login
- Preflight: resume + cookie sync OK (`destHasAuth` SQLite `li_at` name present)
- Live CDP: seed/session invalid → `/login`
- Auto-login: Google session present; Continue with Google **clicked** after welcome-back fix; LinkedIn still served `/checkpoint/challenge` for GSI and password
- Per prompt: CAPTCHA with Google session — do not treat as missing Google SSO setup; owner must pass security check

## Code fix this run
- `tools/linkedin/auto_login.py`: reveal full login form (`Sign in using another account`), prefer Google SSO when Google cookies exist, click visible GSI iframe

## Owner action
1. `bash scripts/home-headed-login.sh linkedin` (or complete security check on `/home/ubuntu/chrome-cdp-profile`)
2. Confirm feed loads with live `li_at`
3. `bash scripts/refresh-portal-session-seed.sh linkedin` and push `.portal-sessions` / Save snapshot
