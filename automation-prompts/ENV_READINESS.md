# Environment readiness for 6 daily job automations

## Verdict (2026-08-06 morning cron audit)

| Item | Status |
| --- | --- |
| Schedulers fired at 9 AM IST (03:30 UTC) | YES — all 6 portal automations + General Daily launched |
| PR #11 install bootstrap on `main` | YES |
| Resume in git | YES — `resumes/Rafi_Resume.docx` |
| Desktop Chrome Default has all 6 logins (this VM) | YES when you logged in |
| Cron CDP profiles had those logins | **NO** — agents used empty `chrome-cdp-profile` / `chrome-foundit` / etc. |
| Cutshort | Applied (1) — only portal that got past auth |
| LinkedIn / Foundit / Instahyre / Indeed | Stopped at login / Cloudflare |
| Naukri | Logged in via Google OAuth; 0 applies (title-filter false skips) |
| Indeed private worker | NO |

**Root cause:** You logged into **Default** Chrome (`~/.config/google-chrome`). Cron agents launch **separate** CDP profiles that were empty. Fix in repo: `scripts/sync-chrome-sessions.sh` copies Default → each CDP profile at start of every run.

## What you must do once (Desktop) so tomorrow works

1. Open Cloud Agent Desktop for [this environment](https://cursor.com/dashboard/cloud-agents/environments/e/545c2557-9097-11f1-ba66-0e7d0216e441).
2. In **normal Chrome** (Default profile), confirm still logged into LinkedIn, Naukri, Foundit, Cutshort, Instahyre, Indeed (home/profile pages, not Sign in).
3. In a terminal on that Desktop run:
   ```bash
   bash scripts/sync-chrome-sessions.sh
   node tools/chrome_session.js status
   ```
   All 6 portals should show `sourceHasAuth: true` and `destHasAuth: true`.
4. **Save / Update snapshot** on the environment dashboard (freeze this disk — including `~/.config/google-chrome` and the synced CDP profiles).
5. Merge the session-sync PR to `main` (or point automations at that branch).
6. Re-paste loaders from `ONE_TIME_LOADERS.md` if prompts were never loaded from repo.
7. **Disable General Daily 9 AM** (it only opens research PRs; 0 applies).
8. Indeed: attach a **private worker** if Cloudflare still blocks.

## Install command (environment dashboard)

Prefer:
```bash
bash scripts/cloud-agent-install.sh
```
(That bootstraps resume, npm tools, and runs session sync when Default cookies exist.)
