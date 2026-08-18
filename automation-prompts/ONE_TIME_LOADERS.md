# One-time loader prompts (paste once — then PRs update behavior)

Cursor Automations **cannot be edited by this cloud agent** (`get-automation` is read-only; there is no update/write tool).  
Paste each block below into the matching automation **once**. After that, merge PRs to `main` (or point the automation at this branch) and the agent will load the latest instructions from the repo files — no more manual re-pastes when we refine prompts.

**Critical for every portal run:** agents must run `bash scripts/preflight-portal-run.sh <portal>` so Desktop Chrome logins are copied into CDP profiles without clobbering existing authenticated profiles. Without authenticated Default Chrome cookies **inside the saved snapshot**, cron hits login walls. Owner check: `bash scripts/verify-portal-logins.sh --strict`.

**Auto-fix & push & merge:** every run must follow [AUTO_FIX.md](AUTO_FIX.md) — code-fixable blockers get durable helper patches, a feature-branch push, a **ready** PR, `bash scripts/auto-merge-fix-pr.sh` (not silent report-only / not draft-only), and a **same-day re-run** of that portal's job via `scripts/rerun-daily-after-fix.sh` so today's applies use the fix.

## Same-day re-runs + missing cron recovery (owner secret)

Set **`CURSOR_API_KEY`** on the Cloud Agent environment ([Dashboard → API Keys](https://cursor.com/dashboard/api)) so:
1. `scripts/auto-merge-fix-pr.sh` → `scripts/rerun-daily-after-fix.sh` can launch a **fresh** cloud job on `main` after a fix (max 5/portal/IST day).
2. `scripts/ensure-missing-daily-runs.sh` can recover when an enabled portal cron (LinkedIn/Cutshort/Instahyre/Indeed/…) never fired that morning.

Without the key, helpers still re-exec durable apply scripts **in the current session**.



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

## Notification Job 11 AM
https://cursor.com/automations/8e34696c-90b1-11f1-ba66-0e7d0216e441

```text
Read and OBEY the full instructions in automation-prompts/07-notification.md (the fenced text block). Compile status from all apply automations and email rafi.success@gmail.com. For Indeed, run `bash scripts/fetch-indeed-home-result.sh --today` first and include applied/external/rejected/blocked/skipped from that home-local JSON (do not use cloud Cloudflare as Indeed when same-day home results exist). Include Hitech City / Knowledge City Daily totals from `/opt/cursor/artifacts/hitechcity-daily.json` when present.
```

## Hitech City / Knowledge City Daily
https://cursor.com/automations/b65968f7-953d-11f1-ba66-0e7d0216e441

Rename this automation in the UI to **Hitech City / Knowledge City Daily** (it is currently Untitled). Paste once:

```text
Read and OBEY the full instructions in automation-prompts/08-hitech-city.md (the fenced text block). Run `bash scripts/preflight-portal-run.sh hitechcity` first, then `bash scripts/launch-chrome-cdp.sh hitechcity`. Use resumes/Rafi_Resume.docx. Execute the daily Hitech City / Knowledge City / Madhapur premium-campus career-portal + LinkedIn referral apply job now via `python3 tools/hitechcity/daily_apply.py` (every run uses parallel multi-tab careers, `HITECHCITY_PARALLEL_TABS=10` by default — do not set tabs=1).
```

## Ensure Missing Daily Runs (~10:30 AM IST) — CREATE THIS
Schedule a new automation after the 9 AM portal wave (before Notification 11 AM). Paste once:

```text
Read and OBEY automation-prompts/09-ensure-missing.md (the fenced text block). Run `bash scripts/ensure-missing-daily-runs.sh` to launch any apply portals that have no usable same-day coverage (cron miss / login-wall reports do not count as done). Needs CURSOR_API_KEY for fresh cloud launches. Do not invent applies. Do not FORCE_RESTORE_SESSIONS.
```

**Already in repo as backup:** GitHub Actions workflow `Ensure Missing Daily Runs` (cron 05:00 UTC / 10:30 IST + manual dispatch) runs the same script when `CURSOR_API_KEY` is set as a repo secret. Still create the Cursor Automation above — agents cannot create Automations via API.

Owner checklist for logins/secrets: [MAX_APPLY_OWNER_CHECKLIST.md](MAX_APPLY_OWNER_CHECKLIST.md).

## Optional: General Daily 9 AM — DISABLE THIS
https://cursor.com/automations/30e2c023-9067-11f1-ba66-0e7d0216e441

This duplicates portal work but only does research/PRs (0 applies). **Disable it** in the Automations UI, or paste the Naukri loader above if you keep it.
