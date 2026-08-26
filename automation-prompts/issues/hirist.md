# Hirist issues log

## 2026-08-26 (cloud)

| Issue | Fix |
| --- | --- |
| Hirist blocked on login with no Gmail SSO / 2FA chat prompt | google_login.js + daily_apply Google SSO; google_2fa_prompt.py ASK_OWNER_GOOGLE_2FA in chat; GOOGLE_AUTH.md |


Portal-scoped log. Append via `bash scripts/append-issue-fix.sh hirist "issue" "fix"`.

| Date | Issue | Fix |
| --- | --- | --- |
| 2026-08-24 | No dedicated Hirist daily automation — Naukri only soft-skipped Hirist CTAs (`hirist_login_required_skip`) | Added `tools/hirist/*` runner + `09-hirist.md`, wired into Daily Apply Portals / home tasks / notification |
