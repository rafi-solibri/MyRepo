# Notification Job 11 AM — paste into Agent instructions

Automation: https://cursor.com/automations/8e34696c-90b1-11f1-ba66-0e7d0216e441

Copy everything inside the block below:

```text
Send a status email to [REDACTED] covering today’s results from ALL job-apply automations.

## Source of truth (HARD — every run)
- **Home-local is DISABLED.** Do NOT run `scripts/fetch-home-result.sh`, `scripts/fetch-indeed-home-result.sh`, or report “home result missing”.
- Primary source: **cloud Cursor Automation / GHA agents** for today. Use `list-cloud-agents` (createdAfter today) + transcripts / `/opt/cursor/artifacts/*` when present on the agent pods.
- Never invent applies. Prefer confirmed ATS / portal submit evidence over redirect-only / Applied-tab bumps.

Cloud automations to include (always):
- LinkedIn Daily 9 AM (beb6ef8e-908f-11f1-ba66-0e7d0216e441)
- Foundit Daily 9 AM (5d1b07b2-90a9-11f1-ba66-0e7d0216e441)
- Cutshort Daily 9 AM (d6ba8b9d-9094-11f1-ba66-0e7d0216e441)
- Naukri Daily 9 AM (003b88eb-909a-11f1-ba66-0e7d0216e441)
- Instahyre Daily 9 AM (1d0ea682-9093-11f1-ba66-0e7d0216e441)
- Indeed Daily (91b09fd7-9093-11f1-ba66-0e7d0216e441)
- Hirist Daily 9 AM — ONE_TIME_LOADERS / GHA Daily Apply Portals
- **Hitech City / Knowledge City Daily (b65968f7-953d-11f1-ba66-0e7d0216e441)** — runs ~11 AM on its own automation. ALWAYS wait/poll this agent and include applied/blocked/skipped (+ `/opt/cursor/artifacts/hitechcity-daily.json` when present on that run). Do not omit Hitech because the JSON is missing on the Notification pod — pull totals from the Hitech agent transcript.

## Counts (honest)
For each portal report: applied, external (company-website **completed**), rejected, blocked (login/Cloudflare/resume/OTP), skipped highlights.
- **Applied = confirmed submit only** (Application submitted / ATS confirmation / native portal success without unfinished redirect). Do NOT treat Foundit Falcon `APPLY_REDIRECT` + `linkedin_no_easy_apply` / `external_incomplete` as applied.
- Split “portal registered / redirect only” vs “ATS completed” when both appear in reports.
- Include blockerSummary + short highlights + agent URLs.
- Note targets: Expected CTC 65 LPA; Hyd + Remote/WFH; resume `Rafi_Resume.docx` (rebuilt every run from `Mohammed_Abdul_Rafi_Ahmed_Resume.docx`, JD-tailored per apply).

Email delivery:
- Prefer Resend MCP → [REDACTED]
- From: RESEND_FROM_EMAIL when set to a verified sender; otherwise use `Job Status <onboarding@resend.dev>` and mention the missing secret
- Subject: Job status — YYYY-MM-DD
- If Resend MCP unavailable but RESEND_API_KEY is set, use scripts/send-job-status-email.mjs
- Always write the full report to automation memory
- Wait/poll still-running apply agents (especially Hitech + Indeed) before sending when possible
- Daily apply launches are owned by GitHub Actions **Daily Apply Portals** (`scripts/launch-daily-portals.sh`, 9:00 AM IST). Do NOT launch missing portals from Notification — only report. If a portal has no same-day agent, say so.

## Auto-fix & push (MANDATORY)
If the mail pipeline itself has a code-fixable bug (send-job-status-email.mjs, prompt formatting), fix under scripts/ or automation-prompts/, append via `bash scripts/append-issue-fix.sh notification "issue" "fix"`, commit + push a feature branch, open a ready PR to main and run `bash scripts/auto-merge-fix-pr.sh`. Follow automation-prompts/AUTO_FIX.md. List today’s open/merged portal fix PRs in the email. Owner-only: missing RESEND secrets / verified domain.
```
