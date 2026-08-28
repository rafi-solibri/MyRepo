# One-time loader prompts (paste once — then PRs update behavior)

Cursor Automations **cannot be edited by this cloud agent** (`get-automation` is read-only; there is no update/write tool).  
Paste each block below into the matching automation **once**. After that, merge PRs to `main` (or point the automation at this branch) and the agent will load the latest instructions from the repo files — no more manual re-pastes when we refine prompts.

**Critical for every portal run:** agents must run `bash scripts/preflight-portal-run.sh <portal>` so Desktop Chrome logins are copied into CDP profiles without clobbering existing authenticated profiles. Without authenticated Default Chrome cookies **inside the saved snapshot**, cron hits login walls. Owner check: `bash scripts/verify-portal-logins.sh --strict`.

**Auto-fix & push & merge:** every run must follow [AUTO_FIX.md](AUTO_FIX.md) — code-fixable blockers get durable helper patches, a feature-branch push, a **ready** PR, `bash scripts/auto-merge-fix-pr.sh` (not silent report-only / not draft-only), and a **same-day re-run** of that portal's job via `scripts/rerun-daily-after-fix.sh` so today's applies use the fix.

## Daily launches + same-day post-fix re-runs (owner secret)

Set **`CURSOR_API_KEY`** on the Cloud Agent environment **and** as a GitHub Actions repo secret ([Dashboard → API Keys](https://cursor.com/dashboard/api)) so:
1. GitHub Actions workflow **Daily Apply Portals** (cron `30 3 * * *` = 9:00 AM IST) runs `scripts/launch-daily-portals.sh` and reliably starts every apply portal.
2. `scripts/auto-merge-fix-pr.sh` → `scripts/rerun-daily-after-fix.sh` can launch a **fresh** cloud job on `main` after a fix (max 5/portal/IST day).

Without the key, helpers still re-exec durable apply scripts **in the current session**, and the Daily Apply Portals workflow will fail until the secret is set.

**Optional:** keep the Cursor Automations below enabled for manual/UI runs. `launch-daily-portals.sh` skips a portal when a same-day agent already exists, so overlapping schedules do not double-launch. There is **no** “Ensure Missing Daily Runs” recovery job anymore.



## LinkedIn Daily 9 AM
https://cursor.com/automations/beb6ef8e-908f-11f1-ba66-0e7d0216e441

```text
Read and OBEY the full instructions in automation-prompts/01-linkedin.md (the fenced text block). Run `bash scripts/preflight-portal-run.sh linkedin` first, then `bash scripts/launch-chrome-cdp.sh linkedin`. Use resumes/Rafi_Resume.docx. Execute the daily LinkedIn apply job now.
```

## Foundit Daily 9 AM
https://cursor.com/automations/5d1b07b2-90a9-11f1-ba66-0e7d0216e441

```text
Read and OBEY the full instructions in automation-prompts/02-foundit.md (the fenced text block). Run `bash scripts/preflight-portal-run.sh foundit` first. Use resumes/Rafi_Resume.docx. Execute the daily Foundit apply job now.
```

## Cutshort Daily 9 AM
https://cursor.com/automations/d6ba8b9d-9094-11f1-ba66-0e7d0216e441

```text
Read and OBEY the full instructions in automation-prompts/03-cutshort.md (the fenced text block). Run `bash scripts/preflight-portal-run.sh cutshort` first. Use resumes/Rafi_Resume.docx. Execute the daily Cutshort apply job now.
```

## Naukri Daily 9 AM
https://cursor.com/automations/003b88eb-909a-11f1-ba66-0e7d0216e441

```text
Read and OBEY the full instructions in automation-prompts/04-naukri-general.md (the fenced text block). Run `bash scripts/preflight-portal-run.sh naukri` first, then `bash scripts/launch-chrome-cdp.sh naukri`. CRITICAL STEP 0: refresh Naukri profile resume with resumes/Rafi_Resume.docx via `node tools/naukri/update_profile_resume.js` (or manual upload on mnjuser/profile) BEFORE applying. Then execute the daily Naukri apply job.
```

## Instahyre Daily 9 AM
https://cursor.com/automations/1d0ea682-9093-11f1-ba66-0e7d0216e441

```text
Read and OBEY the full instructions in automation-prompts/05-instahyre.md (the fenced text block). Run `bash scripts/preflight-portal-run.sh instahyre` first. Use resumes/Rafi_Resume.docx. Execute the daily Instahyre apply job now.
```

## Indeed Daily 9 AM
https://cursor.com/automations/91b09fd7-9093-11f1-ba66-0e7d0216e441

Cloud path uses WARP SOCKS + SeleniumBase UC (`preflight.js` / `daily_apply.js`) after the filelock singleton fix. Home cron (`scripts/indeed-home-daily.sh`) remains a good fallback. **Re-paste this loader** if the Automations UI still has an older short prompt that stops immediately on exit 5 without reading `06-indeed.md`:

```text
Read and OBEY automation-prompts/06-indeed.md (fenced block).
FIRST: `node tools/indeed/preflight.js` (WARP+UC Turnstile clear + filelock patch + IP rotate). If it still exits 5 after that, stop and report — do not invent applies.
Otherwise: `bash scripts/preflight-portal-run.sh indeed`, then `node tools/indeed/daily_apply.js` (preferred) or `python3 tools/indeed/uc_daily_apply.py`.
Use resumes/Rafi_Resume.docx. Report submitted/skipped/blocked.
```

## Hirist Daily 9 AM — OWNER MUST CREATE (still missing as of 2026-08-28)
Unlike LinkedIn/Foundit/etc., **Hirist has no Cursor Automation ID yet**. Without this automation **and** without GitHub Actions secret `CURSOR_API_KEY`, morning Hirist never starts (Notification will recover-launch only when the cloud env has `CURSOR_API_KEY`).

1. Create a new Cursor Automation named **Hirist Daily 9 AM** (cron ~9:00 AM IST).
2. Paste once:

```text
Read and OBEY the full instructions in automation-prompts/09-hirist.md (the fenced text block). Run `bash scripts/preflight-portal-run.sh hirist` first, then `bash scripts/launch-chrome-cdp.sh hirist`. Use resumes/Rafi_Resume.docx. Execute the daily Hirist apply job now via `node tools/hirist/daily_apply.js`.
```

3. Owner once: `bash scripts/home-headed-login.sh hirist` then Save Environment snapshot so cron has a live `token` cookie (session seed currently lacks Hirist).
4. After create, paste the new automation URL/UUID into `automation-prompts/09-hirist.md` + `07-notification.md` + `scripts/rerun-daily-after-fix.sh` `automation_id` for hirist.

## Notification Job 11 AM
https://cursor.com/automations/8e34696c-90b1-11f1-ba66-0e7d0216e441

```text
Read and OBEY the full instructions in automation-prompts/07-notification.md (the fenced text block). Compile status from ALL cloud job-apply automations and email [REDACTED]. Home-local is DISABLED — do NOT run fetch-home-result / fetch-indeed-home-result. Always wait/poll and include Hitech City / Knowledge City Daily (b65968f7-953d-11f1-ba66-0e7d0216e441, ~11 AM) totals from that agent (and hitechcity-daily.json when present). Count only confirmed ATS/portal submits — not Foundit redirect-only.
```

Also include Hirist + Indeed cloud totals (see `07-notification.md`).

## Hitech City / Knowledge City Daily
https://cursor.com/automations/b65968f7-953d-11f1-ba66-0e7d0216e441

Rename this automation in the UI to **Hitech City / Knowledge City Daily** (it is currently Untitled). Paste once:

```text
Read and OBEY the full instructions in automation-prompts/08-hitech-city.md (the fenced text block). Run `bash scripts/preflight-portal-run.sh hitechcity` first, then `bash scripts/launch-chrome-cdp.sh hitechcity`. Use resumes/Rafi_Resume.docx. Execute the daily Hitech City / Knowledge City / Madhapur premium-campus career-portal + LinkedIn referral apply job now via `python3 tools/hitechcity/daily_apply.py` (every run uses parallel multi-tab careers, `HITECHCITY_PARALLEL_TABS=10` by default — do not set tabs=1).
```

## Daily Apply Portals (GitHub Actions — primary 9 AM IST trigger)

No Cursor Automation needed. Workflow `.github/workflows/daily-apply-portals.yml` runs `bash scripts/launch-daily-portals.sh` at **9:00 AM IST**. Requires repo secret `CURSOR_API_KEY`. Manual: Actions → Daily Apply Portals → Run workflow.

If you previously created an **Ensure Missing Daily Runs** Cursor Automation (~10:30 AM IST), **disable or delete it** — that recovery path is removed.

Owner checklist for logins/secrets: [MAX_APPLY_OWNER_CHECKLIST.md](MAX_APPLY_OWNER_CHECKLIST.md).

## Optional: General Daily 9 AM — DISABLE THIS
https://cursor.com/automations/30e2c023-9067-11f1-ba66-0e7d0216e441

This duplicates portal work but only does research/PRs (0 applies). **Disable it** in the Automations UI, or paste the Naukri loader above if you keep it.
