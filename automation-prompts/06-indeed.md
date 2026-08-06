# Indeed Daily 9 AM — paste into Agent instructions

Automation: https://cursor.com/automations/91b09fd7-9093-11f1-ba66-0e7d0216e441

Copy everything inside the block below:

```text
FIRST: run `node tools/indeed/preflight.js`. If it exits 5, stop and report that Indeed needs a private worker / residential IP.
Then run `bash scripts/preflight-portal-run.sh indeed`. Verify `node tools/indeed/resume.js`.
Then run `bash scripts/launch-chrome-cdp.sh indeed` if using browser/CDP.
Chrome CDP profile: /home/ubuntu/chrome-indeed-profile (synced from Desktop Default).

Daily Indeed (in.indeed.com) apply for Mohammed Abdul Rafi Ahmed.

## Resume (HARD)
Upload **Rafi_Resume.docx** on Easy Apply and every company ATS. Bootstrap paths: /workspace/resumes/Rafi_Resume.docx, /home/ubuntu/Documents/Rafi_Resume.docx. Never invent stubs.

## Profile
SA / Technical Architect / Tech Lead / EM / Principal .NET | Hyd + Remote/WFH
Current 52 LPA | Expected 65 LPA | Immediate | +91 8790251698 | rafi.success@gmail.com

## Scope / blockers
- Primary https://in.indeed.com — logged-in session required.
- If Cloudflare "Additional Verification Required" / 403 on datacenter IP: stop and report that Indeed needs a private worker / residential IP + logged-in Chrome profile. Do not invent applies.
- If login missing but page loads: stop and report Indeed login required — Desktop Chrome Default login + sync-chrome-sessions.sh + Save Snapshot; prefer private worker for Cloudflare.

## Apply paths
- Prefer Indeed Easy Apply through confirmation.
- "Apply on company site" / external ATS: FOLLOW and COMPLETE with Rafi_Resume.docx. Do not skip.
- One job at a time; ~3–4 min CAPTCHA cap; continue.

## Location HARD
Hyd/Telangana OR Remote/WFH/India Remote only.

## Filters
Prefer .NET/C# evidence; skip Java/Node/Python-mandatory-only, QA/junior, Salesforce/ServiceNow/SAP-primary, listed max <50L.

## Report
Submitted (Easy Apply vs ATS), skipped, blocked. No invented applies.
```
