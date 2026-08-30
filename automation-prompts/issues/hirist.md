# Hirist issues log

## 2026-08-30 (cloud)

| Issue | Fix |
| --- | --- |
| AI Solution Architect / Data Engineering / ETL titles passed skipReason (no .NET on title) | HARD-skip AI+architect, data engineering, and ETL architect titles without .NET |


## 2026-08-28 (cloud)

| Issue | Fix |
| --- | --- |
| Gmail SSO hung on password page; auth cookie is hirist_seeker_enc not token | Fill Google Passwd via CDP; treat challenge/pwd as password not 2FA; recognize hirist_seeker_enc |
| No Cursor Automation + GHA CURSOR_API_KEY empty → no same-day Hirist agent (other portals fire via Automations) | Notification Hirist recovery launch when CURSOR_API_KEY set; louder ONE_TIME_LOADERS create steps; launch-daily-portals hirist prompt includes CDP; launched Hirist Daily 2026-08-28 via API |


## 2026-08-26 (cloud)

| Issue | Fix |
| --- | --- |
| Hirist blocked on login with no Gmail SSO / 2FA chat prompt | google_login.js + daily_apply Google SSO; google_2fa_prompt.py ASK_OWNER_GOOGLE_2FA in chat; GOOGLE_AUTH.md |


Portal-scoped log. Append via `bash scripts/append-issue-fix.sh hirist "issue" "fix"`.

| Date | Issue | Fix |
| --- | --- | --- |
| 2026-08-24 | No dedicated Hirist daily automation — Naukri only soft-skipped Hirist CTAs (`hirist_login_required_skip`) | Added `tools/hirist/*` runner + `09-hirist.md`, wired into Daily Apply Portals / home tasks / notification |
