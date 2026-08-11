# Notification Job 11 AM — paste into Agent instructions

Automation: https://cursor.com/automations/8e34696c-90b1-11f1-ba66-0e7d0216e441

Copy everything inside the block below:

```text
Send a status email to rafi.success@gmail.com covering today’s results from ALL job-apply automations.

Cloud automations to include:
- LinkedIn Daily 9 AM (beb6ef8e-908f-11f1-ba66-0e7d0216e441)
- Foundit Daily 9 AM (5d1b07b2-90a9-11f1-ba66-0e7d0216e441)
- Cutshort Daily 9 AM (d6ba8b9d-9094-11f1-ba66-0e7d0216e441)
- Naukri Daily 9 AM (003b88eb-909a-11f1-ba66-0e7d0216e441)
- Instahyre Daily 9 AM (1d0ea682-9093-11f1-ba66-0e7d0216e441)
- Hitech City / Knowledge City Daily (b65968f7-953d-11f1-ba66-0e7d0216e441) — campus career portals + LinkedIn referrals; read `/opt/cursor/artifacts/hitechcity-daily.json` / agent run when available

Indeed (IMPORTANT — home/local, not cloud Cloudflare):
- Indeed runs on the home PC via `scripts/indeed-home-daily.sh` (residential IP).
- ALWAYS load those results before composing the mail:
  bash scripts/fetch-indeed-home-result.sh --today
- Parse JSON counts: applied, external, rejected, blocked, skipped (and seen if present).
- Include blockerSummary + short highlights from applied/rejected/blocked/skipped arrays.
- Prefer same-day home-local results (`source: home-local`) for the Indeed section.
- Do NOT treat the cloud Indeed Daily automation (91b09fd7-9093-11f1-ba66-0e7d0216e441) Cloudflare failure as the Indeed result when a same-day home result exists.
- Only if fetch exits non-zero / no same-day home JSON: say “Indeed home result missing” and optionally note the cloud Cloudflare stub — never invent applies.

For each portal: applied, external/company-website completed, rejected, blocked (login/Cloudflare/resume/OTP), skipped highlights, agent run links (home Indeed: mention automation-results branch / latest.json date).
Note targets: Expected CTC 65 LPA; Hyd + Remote/WFH; resume file Rafi_Resume.docx.

Email delivery:
- Prefer Resend MCP → rafi.success@gmail.com
- From: RESEND_FROM_EMAIL when set to a verified sender; otherwise use the documented fallback `Job Status <onboarding@resend.dev>` and mention the missing secret in the report
- Subject: Job status — YYYY-MM-DD
- If Resend MCP unavailable but RESEND_API_KEY is set, use scripts/send-job-status-email.mjs as fallback
- Always write the full report to automation memory
- Do not invent findings; wait/poll still-running apply agents before sending when possible

## Auto-fix & push (MANDATORY)
If the mail pipeline itself has a code-fixable bug (fetch-indeed-home-result.sh, send-job-status-email.mjs, prompt formatting), fix under scripts/ or automation-prompts/, append ISSUES_AND_FIXES.md, commit + push a feature branch, open a draft PR to main. Follow automation-prompts/AUTO_FIX.md. Also list any open portal fix PRs from today’s apply agents in the email. Owner-only: missing RESEND secrets / verified domain.
```
