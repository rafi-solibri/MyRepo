# Notification Job 11 AM — paste into Agent instructions

Automation: https://cursor.com/automations/8e34696c-90b1-11f1-ba66-0e7d0216e441

Copy everything inside the block below:

```text
Send a status email to rafi.success@gmail.com covering today’s results from ALL job-apply automations.

Preferred source: HOME-LOCAL Task Scheduler runs (see automation-prompts/HOME_AUTOMATIONS.md).
For EACH portal, load same-day JSON before composing the mail:

Cloud automations to include:
- LinkedIn Daily 9 AM (beb6ef8e-908f-11f1-ba66-0e7d0216e441)
- Foundit Daily 9 AM (5d1b07b2-90a9-11f1-ba66-0e7d0216e441)
- Cutshort Daily 9 AM (d6ba8b9d-9094-11f1-ba66-0e7d0216e441)
- Naukri Daily 9 AM (003b88eb-909a-11f1-ba66-0e7d0216e441)
- Instahyre Daily 9 AM (1d0ea682-9093-11f1-ba66-0e7d0216e441)
- Hitech City / Knowledge City Daily (b65968f7-953d-11f1-ba66-0e7d0216e441) — campus career portals + LinkedIn referrals; read `/opt/cursor/artifacts/hitechcity-daily.json` / agent run when available

  bash scripts/fetch-home-result.sh linkedin --today
  bash scripts/fetch-home-result.sh foundit --today
  bash scripts/fetch-home-result.sh cutshort --today
  bash scripts/fetch-home-result.sh naukri --today
  bash scripts/fetch-home-result.sh instahyre --today
  bash scripts/fetch-home-result.sh indeed --today

Legacy Indeed helper still works: `bash scripts/fetch-indeed-home-result.sh --today`

Parse JSON counts: applied, external, rejected, blocked, skipped (and seen if present).
Include blockerSummary + short highlights. Prefer `source: home-local` same-day results.
If a portal fetch fails / no same-day JSON: say “<portal> home result missing” — never invent applies.
Do NOT treat cloud Cloudflare/login failures as the result when a same-day home JSON exists.

Optional cloud automation ids (only if home JSON missing and you still have cloud runs):
- LinkedIn beb6ef8e-908f-11f1-ba66-0e7d0216e441
- Foundit 5d1b07b2-90a9-11f1-ba66-0e7d0216e441
- Cutshort d6ba8b9d-9094-11f1-ba66-0e7d0216e441
- Naukri 003b88eb-909a-11f1-ba66-0e7d0216e441
- Instahyre 1d0ea682-9093-11f1-ba66-0e7d0216e441
- Indeed 91b09fd7-9093-11f1-ba66-0e7d0216e441

For each portal: applied, external/company-website completed, rejected, blocked (login/Cloudflare/resume/OTP), skipped highlights, and automation-results/<portal>/latest.json date when home-local.
Note targets: Expected CTC 65 LPA; Hyd + Remote/WFH; resume file Rafi_Resume.docx.

Email delivery:
- Prefer Resend MCP → rafi.success@gmail.com
- From: RESEND_FROM_EMAIL when set to a verified sender; otherwise use the documented fallback `Job Status <onboarding@resend.dev>` and mention the missing secret in the report
- Subject: Job status — YYYY-MM-DD
- If Resend MCP unavailable but RESEND_API_KEY is set, use scripts/send-job-status-email.mjs as fallback
- Always write the full report to automation memory
- Do not invent findings; wait/poll still-running apply agents before sending when possible

## Auto-fix & push (MANDATORY)
If the mail pipeline itself has a code-fixable bug (fetch-indeed-home-result.sh, send-job-status-email.mjs, prompt formatting), fix under scripts/ or automation-prompts/, append via `bash scripts/append-issue-fix.sh <portal> "issue" "fix"`, commit + push a feature branch, open a ready PR to main and run `bash scripts/auto-merge-fix-pr.sh`. That merge helper then same-day re-runs this Notification Job with the fix (`scripts/rerun-daily-after-fix.sh`) — do not wait for tomorrow's cron. Follow automation-prompts/AUTO_FIX.md. Also list any open/merged portal fix PRs from today’s apply agents in the email. Owner-only: missing RESEND secrets / verified domain.
```
