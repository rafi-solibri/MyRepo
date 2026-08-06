# Naukri Daily 9 AM — paste into Agent instructions

Automation: https://cursor.com/automations/003b88eb-909a-11f1-ba66-0e7d0216e441
(Also use for General Daily 9 AM if still enabled: https://cursor.com/automations/30e2c023-9067-11f1-ba66-0e7d0216e441)

Copy everything inside the block below:

```text
FIRST: run `bash scripts/bootstrap-job-assets.sh`. Verify `node tools/naukri/resume_and_filters.js`.
Chrome CDP: copy profile to /home/ubuntu/.naukri-chrome-profile (default profile rejects DevTools). --disable-extensions.

Daily Naukri + company-ATS apply for Mohammed Abdul Rafi Ahmed. Hyd + Remote/WFH. Expected CTC 65 LPA.

## Resume (HARD)
- Canonical **Rafi_Resume.docx** at resumes/Rafi_Resume.docx and /home/ubuntu/Documents/Rafi_Resume.docx after bootstrap.
- Upload this file on every company ATS. Do not rely only on Naukri hosted resume for external applies.
- Never invent a stub. Do not require Rafi_Resume_Architect.docx.

## Profile
Phone +91 8790251698 | rafi.success@gmail.com | Current 52 LPA | Expected 65 LPA | Immediate
Stack: .NET Core/C#, AWS/Azure, Kafka/RabbitMQ, K8s, React/Angular | 15+ years

## Primary board
1. https://www.naukri.com — must be logged in. If login/OTP: use Gmail in same Chrome profile for OTP, then continue. If impossible, stop and report.
2. Newest 1d→3d→7d. Filters Hyd/Secunderabad + Remote/WFH. Exp ~10–20.
3. Queries: Solution Architect .NET, Technical Architect .NET, .NET Technical Lead, Engineering Manager .NET, Principal Engineer .NET, Azure Architect .NET

## TopTier UI
- Cards are div.cursor-pointer (not classic job-listings links). Quick Apply opens a popup.
- Success = detail CTA shows Applied. Sidebar "Applied (N)" is a FILTER CHIP — never use as per-job status.
- Use tools/naukri/resume_and_filters.js for .NET proof + Coupa/Pega/SAP/Salesforce skips (Intern must not match Internet).

## Apply paths (CRITICAL)
- Naukri Quick Apply when it submits on Naukri.
- If "On company site" / Workday / Greenhouse / Lever / SmartRecruiters / SuccessFactors / etc.: OPEN and COMPLETE with Rafi_Resume.docx + 52/65/immediate/Hyd. Log each redirect URL + outcome. Do not end the day at 0 external without trying.
- Cap CAPTCHA/login walls ~3–4 min → blocked → continue.
- After apply, attempt contact recruiter / chat with 15–20 min screen ask.

## Location HARD
Hyd/Telangana OR Remote/WFH only.

## Report
Every submit: company, role, id/URL, location, Naukri vs ATS path, resume file used. Counts applied/external/blocked/skipped.
```
