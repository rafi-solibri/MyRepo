# Environment readiness for 6 daily job automations

## Current status (2026-08-10)

Portal auth cookies are seeded via `.portal-sessions/` + `scripts/restore-portal-sessions.sh` on install/start. On a healthy snapshot, `bash scripts/verify-portal-logins.sh --strict` and `/opt/cursor/artifacts/portal-login-status.json` should show all 6 portals OK.

If any portal shows FAIL after a rebuild, re-login on Desktop Default Chrome and Save/Update the environment snapshot.

## Historical note (2026-08-06 — fixed)

Earlier snapshots only had Cutshort auth; LinkedIn/Naukri/Foundit/Instahyre/Indeed hit Sign-in walls. Fixed with:
- `.portal-sessions/` cookie seed restored on install/start
- Non-destructive `scripts/sync-chrome-sessions.sh`
- `scripts/preflight-portal-run.sh` + `scripts/verify-portal-logins.sh`

## What to do if logins fail again

```bash
# 1) Open Default Chrome with the 6 portal tabs + checklist
bash scripts/open-portal-login-tabs.sh

# 2) In Cloud Agent Desktop, sign into every FAIL portal until the
#    home/feed/dashboard loads (not a Sign-in page).

# 3) Quit Chrome completely, then verify:
bash scripts/verify-portal-logins.sh --strict

# 4) All 6 must show OK. Then click Save / Update snapshot on:
#    https://cursor.com/dashboard/cloud-agents/environments/e/545c2557-9097-11f1-ba66-0e7d0216e441
```

Optional check:
```bash
node tools/chrome_session.js status
```

## Cron / automation behavior

Every portal run must start with:
```bash
bash scripts/preflight-portal-run.sh <portal>
```

`sync-chrome-sessions.sh` copies authenticated Default Chrome cookies into each CDP profile. It is **non-destructive**: if Default lacks a portal cookie, it will not wipe an already-authenticated CDP profile.

## Other blockers

| Item | Status |
| --- | --- |
| Resume in git | YES — `resumes/Rafi_Resume.docx` |
| Install bootstrap | `bash scripts/cloud-agent-install.sh` |
| Indeed Cloudflare on public cloud IP | Keep **cloud Indeed automation OFF**; use home cron / private worker / `INDEED_HTTP_PROXY` |
| General Daily 9 AM | Keep **disabled** (research-only, 0 applies) |
| Notification sender | Set secret `RESEND_FROM_EMAIL` (verified) + Resend MCP |
| Same-day post-fix re-run | Set secret `CURSOR_API_KEY` (https://cursor.com/dashboard/api) so `scripts/rerun-daily-after-fix.sh` can launch a fresh cloud job on `main` after a merge. Without it, the helper re-executes the durable apply runner in the current session. |

## Environment commands (dashboard)

**Install** (durable baseline — Python + Playwright + Chromium, resume assets, npm tools, CDP profile dirs). With environment builds this runs once at build time:
```bash
bash scripts/cloud-agent-install.sh
```

**Start** (per-boot session reconciliation — copies Desktop Chrome Default logins into each portal CDP profile on every boot so cron agents don't hit login walls):
```bash
bash scripts/cloud-agent-start.sh
```
