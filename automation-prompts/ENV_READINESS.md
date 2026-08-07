# Environment readiness for 6 daily job automations

## Live diagnosis (2026-08-06 — this snapshot)

Verified on the Cloud Agent VM that boots from the **saved** environment build:

| Portal | Auth cookie present? | Evidence |
| --- | --- | --- |
| Cutshort | YES | `cutshort_authentication` |
| LinkedIn | **NO** | only marketing cookies (`bcookie`, `lidc`); **no `li_at`** → Sign-in wall |
| Naukri | **NO** | zero Naukri cookies (Google account cookies alone are not enough) |
| Foundit | **NO** | zero Foundit cookies |
| Instahyre | **NO** | zero Instahyre cookies |
| Indeed | **NO** | zero Indeed auth cookies |

**Why “I logged in on Desktop and Saved” still fails:** Saving install/config is not the same as capturing portal sessions. Cron agents only see cookies that exist in `~/.config/google-chrome/Default` **inside the saved snapshot**. On the current snapshot, 5/6 portals are not authenticated. Visiting login pages without completing sign-in also does not create auth cookies.

## What you must do now (on this Desktop)

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

## Cron / automation behavior after snapshot is fixed

Every portal run must start with:
```bash
bash scripts/preflight-portal-run.sh <portal>
# or:
bash scripts/bootstrap-job-assets.sh
bash scripts/sync-chrome-sessions.sh
```

`sync-chrome-sessions.sh` copies authenticated Default Chrome cookies into each CDP profile (`chrome-cdp-profile`, `.naukri-chrome-profile`, etc.). It is **non-destructive**: if Default lacks a portal cookie, it will not wipe an already-authenticated CDP profile.

## Other blockers

| Item | Status |
| --- | --- |
| Resume in git | YES — `resumes/Rafi_Resume_Technical_Architect.docx` |
| Install bootstrap | `bash scripts/cloud-agent-install.sh` |
| Indeed Cloudflare on public cloud IP | Needs **private / residential worker** |
| General Daily 9 AM | Disable (research-only, 0 applies) |
| Notification sender | Set secret `RESEND_FROM_EMAIL` |

## Session seed (why Save kept failing)

Desktop logins on a running agent do **not** enter environment builds until the
build disk contains those Chrome cookies. Saving install/start alone rebuilds
from the old base (Cutshort-only) and drops the other portals.

Fix in this repo: private `.portal-sessions/` cookie seed + `scripts/restore-portal-sessions.sh`
runs during install/start so every new build restores all 6 portal sessions.

## Environment commands (dashboard)

**Install** (durable baseline — Python + Playwright + Chromium, resume assets, npm tools, CDP profile dirs). With environment builds this runs once at build time:
```bash
bash scripts/cloud-agent-install.sh
```

**Start** (per-boot session reconciliation — copies Desktop Chrome Default logins into each portal CDP profile on every boot so cron agents don't hit login walls):
```bash
bash scripts/cloud-agent-start.sh
```
The start hook is best-effort and never blocks boot: it only syncs when Desktop Chrome has a `Default/Cookies` DB. Log into the portals in Desktop Chrome once, then Save/Update the environment snapshot so the logins persist into future boots.
