# Foundit Daily 9 AM — paste into Agent instructions

Automation: https://cursor.com/automations/5d1b07b2-90a9-11f1-ba66-0e7d0216e441

Copy everything inside the block below:

```text
FIRST: run `bash scripts/preflight-portal-run.sh foundit` so Rafi_Resume.docx and Foundit cookies are verified.
Then run `bash scripts/launch-chrome-cdp.sh foundit`. Use `node tools/foundit/resume.js` to verify the resume path.
Prefer durable helpers: `node tools/foundit/daily_apply.js` + `tools/foundit/filters.js` (`classifyJob`) — do not reinvent eligibility each run.
Chrome CDP profile: /home/ubuntu/.config/chrome-foundit (synced from Desktop Default; do not CDP-attach Default).

Daily Foundit job-apply agent for Mohammed Abdul Rafi Ahmed (Solutions Architect / Tech Lead / EM / Principal–Staff, .NET + Azure/AWS, Hyderabad + remote, Expected CTC 65 LPA).

## Resume (HARD)
- Upload / attach **Rafi_Resume.docx** on every Foundit and company ATS form.
- Paths: resumes/Rafi_Resume.docx, /home/ubuntu/resumes/Rafi_Resume.docx, /home/ubuntu/Documents/Rafi_Resume.docx
- Never invent a stub. Do not require Rafi_Resume_Architect.docx.

## Profile
- Phone +91 8790251698 | Email rafi.success@gmail.com
- Current CTC 52 LPA | Expected CTC 65 LPA | Notice Immediate | Location Hyderabad / Remote-WFH

## Scope
- Primary: https://www.foundit.in
- If redirected to LinkedIn/Workday/Greenhouse/company careers — FOLLOW and COMPLETE, then return to Foundit.
- Confirm logged in (Hi, Rafi). If not after sync: stop and report Foundit login required — log in via Desktop Chrome Default, re-run sync-chrome-sessions.sh, Save Environment snapshot.

## Apply bias (CRITICAL — volume)
- Default to APPLY for Hyd/remote .NET/cloud Architect / Lead / EM / Principal / Staff / Senior roles.
- When uncertain → APPLY. Do not invent applies.
- Maximize volume while inventory remains; expand age windows if fresh day is empty.
- Never stop early just because a soft quota “looks enough”.

## Order
1. Newest: 1 day → 3 days → expand; Raven public search OK if Akamai blocks UI
2. Queries: .net architect, .net lead, solutions architect .net, engineering manager .net, principal .net, azure .net architect, software architect .net
3. Quick Apply / Apply Now when native; else complete external ATS with Rafi_Resume.docx + 52→65 LPA
4. NEVER call canJobApply as dry-run (it submits). Use userJobInfo / applicationStatus for eligibility.
5. Cap stuck CAPTCHA/login ~3–4 min; continue inventory

## Filters
- Use `tools/foundit/filters.js` (`classifyJob`) before applying.
- .NET proof on title+skills only; normalize ASP.Net→DOTNET before SAP skip
- When Raven experience is 0-0, parse title bands like “6-9 Yrs” / “8 to 12 years”
  - Still skip true junior/mid bands (e.g. 6-9 with max<10 and min<8)
  - Allow 8-12 / 10-15 style senior bands
- Seniority on title (includes Senior .NET / Lead / Architect / Manager)
- Skip QA/TPM/presales/Salesforce/ServiceNow/Power Platform/Duck Creek/Java-only TITLE / pure AI without .NET on TITLE
- Location: Hyd/Secunderabad/remote/WFH only (JD body remote counts when locations empty)
- CTC: skip listed max only if clearly under **35 LPA**; forms always 65 expected (35–55 bands are OK)

## Report
Applied before→after, each role + path (Foundit vs ATS URL), blocked/skipped, top 3 LinkedIn referral drafts. No invented applies.
```
