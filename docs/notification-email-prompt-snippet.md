# Prompt snippet — paste into Notification Job 11 AM

```text
After compiling the job-status summary, deliver results by email:

Use the Resend MCP to email rafi.success@gmail.com.
From address: the verified domain address from RESEND_FROM_EMAIL (never invent a From domain).
Subject: Job status — YYYY-MM-DD
Body must include:
- Totals per automation (applied / blocked / skipped)
- Important failures or follow-ups
- Link to this agent run

Always send the email when the run completes, including partial or failed results.
Do not invent findings.
Do not send any other emails.
```
