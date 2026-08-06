# Notification Job 11 AM — paste into Agent instructions

Automation: https://cursor.com/automations/8e34696c-90b1-11f1-ba66-0e7d0216e441

Copy everything inside the block below:

```text
Send a status email to rafi.success@gmail.com covering today’s results from ALL job-apply automations.

Automations to include:
- LinkedIn Daily 9 AM (beb6ef8e-908f-11f1-ba66-0e7d0216e441)
- Foundit Daily 9 AM (5d1b07b2-90a9-11f1-ba66-0e7d0216e441)
- Cutshort Daily 9 AM (d6ba8b9d-9094-11f1-ba66-0e7d0216e441)
- Naukri Daily 9 AM (003b88eb-909a-11f1-ba66-0e7d0216e441)
- Instahyre Daily 9 AM (1d0ea682-9093-11f1-ba66-0e7d0216e441)
- Indeed Daily 9 AM (91b09fd7-9093-11f1-ba66-0e7d0216e441)

For each: applied, external/company-website completed, blocked (login/Cloudflare/resume/OTP), skipped highlights, agent run links.
Note targets: Expected CTC 65 LPA; Hyd + Remote/WFH; resume file Rafi_Resume.docx.

Email delivery:
- Prefer Resend MCP → rafi.success@gmail.com
- From: RESEND_FROM_EMAIL when set to a verified sender; otherwise use the documented fallback `Job Status <onboarding@resend.dev>` and mention the missing secret in the report
- Subject: Job status — YYYY-MM-DD
- If Resend MCP unavailable but RESEND_API_KEY is set, use scripts/send-job-status-email.mjs as fallback
- Always write the full report to automation memory
- Do not invent findings; wait/poll still-running apply agents before sending when possible
```
