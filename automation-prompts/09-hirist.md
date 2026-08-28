# Hirist Daily 9 AM — paste into Agent instructions

**Status (2026-08-28):** No Cursor Automation UUID yet — owner must create **Hirist Daily 9 AM** from [ONE_TIME_LOADERS.md](ONE_TIME_LOADERS.md). Until then, launches come from GHA Daily Apply Portals (needs repo secret `CURSOR_API_KEY`) or Notification Hirist recovery (`launch-daily-portals.sh --portal hirist`).

Create a new Cursor Automation named **Hirist Daily 9 AM** (cron ~9:00 AM IST).  
This cloud agent cannot write Automations UI — paste the loader from ONE_TIME_LOADERS.md once after merge.

Copy everything inside the block below:

```text
FIRST: run `bash scripts/preflight-portal-run.sh hirist`. Verify `node tools/hirist/resume.js`.
Then run `bash scripts/launch-chrome-cdp.sh hirist`.
Prefer durable helper: `node tools/hirist/daily_apply.js` + `node tools/hirist/filters.js` (`skipReason`) + shared `tools/resume_tailor.js` for external ATS.
Chrome CDP profile: /home/ubuntu/chrome-hirist-profile (synced from Desktop Default; do not CDP-attach Default).

Daily Hirist (hirist.tech) apply for Mohammed Abdul Rafi Ahmed. Maximize applies + interview callbacks.

## Resume (HARD)
Upload **Rafi_Resume.docx** on every company ATS redirect. Paths after bootstrap: /workspace/resumes/Rafi_Resume.docx, /home/ubuntu/resumes/Rafi_Resume.docx, /home/ubuntu/Documents/Rafi_Resume.docx. Never invent stubs.
**Per-job JD tailor (default ON)** for external ATS via `tools/resume_tailor.js`. Disable with `HIRIST_TAILOR=0`.

## Profile
SA / Tech Lead / EM / Principal–Staff | .NET + Azure/AWS | Hyd + Remote/WFH
Current 52 LPA | Expected 65 LPA | Immediate | +91 8790251698

## Scope
- https://www.hirist.tech/ (+ gladiator.hirist.tech/job search & apply-multiple APIs)
- Must be logged in. Prefer **Gmail / Continue with Google**: `node tools/hirist/google_login.js` (wired from `daily_apply.js`). Email OTP via `tools/ats/email_otp.py`. On Google 2FA/authenticator, print `ASK_OWNER_GOOGLE_2FA (hirist)` in chat and wait (`tools/google_2fa_prompt.py`) so the owner can enter the code from mobile. See `automation-prompts/GOOGLE_AUTH.md`.
- If Google SSO still fails: stop and report Hirist login required — `bash scripts/home-headed-login.sh hirist`, then sync-chrome-sessions / Save Environment snapshot.
- External ATS redirects: COMPLETE to submitted confirmation — do not count redirect-only.
- Newest first; Hyd then Remote/WFH (`workFromHome`).

## Apply bias (CRITICAL)
- Default to APPLY for Hyd/remote Architect / Tech Lead / EM / Principal / Staff / Senior .NET/cloud.
- When uncertain → APPLY. Title-first skips only. Do not invent applies.
- Keep sweeping QUERY_WAVES while inventory remains.

## Apply paths
- In-app Hirist apply via `POST /job/apply-multiple` when logged in.
- Company website / ATS `applyUrl` redirects: COMPLETE with Rafi_Resume.docx + 52→65. Do not skip.
- Cap stuck external flows ~3–4 min; continue.

## Filters
Prefer .NET/C#/ASP.NET + architect/lead/EM. Use `node tools/hirist/filters.js` / `skipReason`.
HARD skip titles: QA/SDET; Salesforce/ServiceNow/SAP-primary; pure AI/data TITLE without .NET on the TITLE; Java-primary without .NET; non-Hyd non-remote.
Skip listed max only if clearly under **35 LPA** (forms always 65 expected).

## Report
Write `/opt/cursor/artifacts/hirist-apply-report.json` and `hirist-daily-run.json` with applied / external / rejected / blocked / skipped / seen. No invented applies.

## Auto-fix & push (MANDATORY)
If you hit a code-fixable blocker (filters.js / skipReason, daily_apply.js, resume path, CDP login waiter), fix durable helpers under tools/hirist or scripts/, append via `bash scripts/append-issue-fix.sh hirist "issue" "fix"`, commit + push a feature branch, open a ready PR to main and run `bash scripts/auto-merge-fix-pr.sh`. That merge helper then same-day re-runs this Hirist job with the fix (`scripts/rerun-daily-after-fix.sh`) — do not wait for tomorrow's cron. Follow automation-prompts/AUTO_FIX.md. Do not invent applies. Owner-only: login walls, CAPTCHA/OTP.
```
