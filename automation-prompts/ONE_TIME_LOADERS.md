# One-time loader prompts (paste once — then PRs update behavior)

Cursor Automations **cannot be edited by this cloud agent** (`get-automation` is read-only; there is no update/write tool).  
Paste each block below into the matching automation **once**. After that, merge PRs to `main` (or point the automation at this branch) and the agent will load the latest instructions from the repo files — no more manual re-pastes when we refine prompts.

**Critical for every portal run:** agents must run `bash scripts/preflight-portal-run.sh <portal>` so Desktop Chrome logins are copied into CDP profiles without clobbering existing authenticated profiles. Without authenticated Default Chrome cookies **inside the saved snapshot**, cron hits login walls. Owner check: `bash scripts/verify-portal-logins.sh --strict`.

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

**Recommended on individual plans:** turn this automation **Off** in the UI.
Public-cloud cron hits Indeed Cloudflare. Run Indeed instead from **Cursor Desktop on home Wi‑Fi** (see `INDEED_CLOUDFLARE.md` → “Easiest free fix”).

If you keep the automation enabled (will keep failing until residential proxy / Enterprise pool):

```text
Read and OBEY the full instructions in automation-prompts/06-indeed.md (the fenced text block). Run `node tools/indeed/preflight.js` first; if it exits 5, STOP and report Cloudflare Request Blocked — disable this cloud automation and run Indeed from Cursor Desktop on home Wi‑Fi (automation-prompts/INDEED_CLOUDFLARE.md). Otherwise run `bash scripts/preflight-portal-run.sh indeed`. Use resumes/Rafi_Resume.docx. Execute the daily Indeed apply job now.
```

## Notification Job 11 AM
https://cursor.com/automations/8e34696c-90b1-11f1-ba66-0e7d0216e441

```text
Read and OBEY the full instructions in automation-prompts/07-notification.md (the fenced text block). Compile status from all apply automations and email rafi.success@gmail.com.
```

## Optional: General Daily 9 AM — DISABLE THIS
https://cursor.com/automations/30e2c023-9067-11f1-ba66-0e7d0216e441

This duplicates portal work but only does research/PRs (0 applies). **Disable it** in the Automations UI, or paste the Naukri loader above if you keep it.
