# Instahyre Daily 9 AM — paste into Agent instructions

Automation: https://cursor.com/automations/1d0ea682-9093-11f1-ba66-0e7d0216e441

Copy everything inside the block below:

```text
FIRST: run `bash scripts/preflight-portal-run.sh instahyre`. Verify `node tools/instahyre/resume.js`.
Then run `bash scripts/launch-chrome-cdp.sh instahyre`.
Prefer durable helper: `node tools/instahyre/daily_apply.js` + `node tools/instahyre/filters.js` (`skipReason`).
Chrome CDP profile: /home/ubuntu/chrome-instahyre-profile (synced from Desktop Default; do not CDP-attach Default).

Daily Instahyre apply for Mohammed Abdul Rafi Ahmed. Maximize applies + interview callbacks.

## Resume (HARD)
Upload **Rafi_Resume.docx** on Instahyre and every company ATS. Paths after bootstrap: /workspace/resumes/Rafi_Resume.docx, /home/ubuntu/resumes/Rafi_Resume.docx, /home/ubuntu/Documents/Rafi_Resume.docx. Never invent stubs.

## Profile
SA / Tech Lead / EM / Principal–Staff | .NET + Azure/AWS | Hyd + Remote/WFH
Current 52 LPA | Expected 65 LPA | Immediate | +91 8790251698 | rafi.success@gmail.com

## Scope
- https://www.instahyre.com/candidate/opportunities/
- Must be logged in. If login wall after sync: try INSTAHYRE_EMAIL/PASSWORD secrets if present; else stop and report Instahyre login required — log in via Desktop Chrome Default, sync-chrome-sessions.sh, Save Environment snapshot.
- Newest first; Hyd then Remote/WFH.

## Apply bias (CRITICAL)
- Default to APPLY for Hyd/remote Architect / Tech Lead / EM / Principal / Staff / Senior .NET/cloud.
- When uncertain → APPLY. Title-first skips only. Do not invent applies.
- Keep sweeping while inventory remains; expand queries beyond exact ".NET" if Hyd/remote senior roles remain.

## Apply paths
- In-app Apply / Express interest when it fully submits.
- Company website / ATS redirects: COMPLETE with Rafi_Resume.docx + 52→65. Do not skip.
- Cap stuck flows ~3–4 min; continue.

## Filters
Prefer .NET/C#/ASP.NET + architect/lead/EM. Use `node tools/instahyre/filters.js` / `skipReason`.
HARD skip titles: Quality Engineering / Quality Assurance / QA Lead / SDET; Salesforce/ServiceNow/SAP-primary; pure AI/data TITLE without .NET on the TITLE; non-Hyd non-remote.
Skip listed max only if clearly under **35 LPA** (forms always 65 expected).
Do NOT skip because JD casually mentions Java/Salesforce/data as adjacent tech.

## Report
Submitted (path Instahyre vs ATS), skipped, blocked. No invented applies.
```
