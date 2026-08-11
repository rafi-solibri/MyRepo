# Cutshort home daily 2026-08-11

**STOP: Cutshort login/session missing (stale CDP cookie).**

- Preflight: `destHasAuth: true` (SQLite name present) but live CDP redirected to login
- URL: `https://cutshort.io/?redirect_url=%2Fprofile%2Fcandidate-dashboard`
- Applied: 0 | Seen: 0 | Blocked: 1
- Owner action: sign in in the headed Chrome tab (`https://cutshort.io/login`), then re-run `node tools/cutshort/daily_apply.js`
- Helper: `bash scripts/home-headed-login.sh cutshort`

JSON: `artifacts/cutshort-daily-run.json` → published `automation-results/cutshort/2026-08-11.json`
