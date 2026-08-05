# Prompt snippet — paste into Notification Job 11 AM

```text
After compiling the job-status summary, email results to rafi.success@gmail.com.

Preferred: use the Resend MCP if it is enabled on this automation.
Fallback: if RESEND_API_KEY is available in the environment, run:
  RESEND_FROM_EMAIL="${RESEND_FROM_EMAIL:-Job Status <onboarding@resend.dev>}" \
  node scripts/send-job-status-email.mjs \
    --to rafi.success@gmail.com \
    --subject "Job status — YYYY-MM-DD" \
    --body-file <path-to-report.md>

From address: RESEND_FROM_EMAIL, or Job Status <onboarding@resend.dev> for the send-only key.
Subject: Job status — YYYY-MM-DD
Body must include:
- Totals per automation (applied / blocked / skipped)
- Important failures or follow-ups
- Link to this agent run

Always send the email when the run completes, including partial or failed results.
Do not invent findings.
Do not send any other emails.
Do not print, commit, or log the Resend API key.
```
