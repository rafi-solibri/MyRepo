# Naukri Daily 9 AM — paste into Agent instructions

Automation: https://cursor.com/automations/003b88eb-909a-11f1-ba66-0e7d0216e441
General Daily 9 AM (`30e2c023-9067-11f1-ba66-0e7d0216e441`) is duplicate/noisy; disable it in the Automations UI.

Copy everything inside the block below:

```text
FIRST: run `bash scripts/preflight-portal-run.sh naukri`. Verify `node tools/naukri/resume_and_filters.js`.
Then run `bash scripts/launch-chrome-cdp.sh naukri`.
Chrome CDP profile: /home/ubuntu/.naukri-chrome-profile (synced from Desktop Default; Default rejects DevTools). Port 9222.
Title skips: use job title / job-panel text only — never full document.body (sidebar "Software & QA" false-skips SA roles). Prefer `shouldSkipTitle` / `shouldSkipTitleFromDetail` from resume_and_filters.js.

Daily Naukri + company-ATS apply for Mohammed Abdul Rafi Ahmed. Hyd + Remote/WFH. Expected CTC 65 LPA.

## Resume (HARD)
- Canonical **Rafi_Resume.docx** at resumes/Rafi_Resume.docx and /home/ubuntu/Documents/Rafi_Resume.docx after bootstrap.
- Upload this file on every company ATS. Never invent a stub. Do not require Rafi_Resume_Architect.docx.

## STEP 0 — Naukri profile resume refresh (HARD — do before any job applies)
Goal: recruiters see an updated resume / “Updated today” every morning so the profile looks actively looking and ranks better for interview calls.

1. Confirm Naukri login (Hi / profile name). If login/OTP: use Gmail in same Chrome profile; if impossible, stop and report.
2. Run: `node tools/naukri/update_profile_resume.js`
   - Or manually: open https://www.naukri.com/mnjuser/profile → Upload/Update resume → attach **Rafi_Resume.docx** (`#attachCV` / `#lazyAttachCV` / file input) → confirm.
3. Also soft-touch Resume Headline (open edit → Save same/equivalent headline) so last-updated advances if file upload alone does not.
4. Verify success: profile shows resume name containing Rafi_Resume / .docx AND/or update date = today. Write result to `/opt/cursor/artifacts/naukri-profile-resume.json`.
5. If profile resume update fails, report it clearly, then CONTINUE with job applies (do not abort the whole day unless login is missing).
6. Do this EVERY daily run even if the file content is unchanged — re-upload is the point (freshness signal).

## Profile
Phone +91 8790251698 | rafi.success@gmail.com | Current 52 LPA | Expected 65 LPA | Immediate
Stack: .NET Core/C#, AWS/Azure, Kafka/RabbitMQ, K8s, React/Angular | 15+ years
Preferred resume headline (keep / restore if wiped):
Solutions Architect & Technical Lead - 15+ Yrs - .NET Core, Microservices, AWS&Azure, Kafka&RabbitMQ

## Primary board (after STEP 0)
1. Newest 1d→3d→7d. Filters Hyd/Secunderabad + Remote/WFH. Exp ~10–20.
2. Queries: Solution Architect .NET, Technical Architect .NET, .NET Technical Lead, Engineering Manager .NET, Principal Engineer .NET, Azure Architect .NET

## TopTier UI
- Cards are div.cursor-pointer. Quick Apply opens a popup.
- Success = detail CTA shows Applied. Sidebar "Applied (N)" is a FILTER CHIP — never per-job status.
- Use tools/naukri/resume_and_filters.js for .NET proof + Coupa/Pega/SAP/Salesforce skips (Intern must not match Internet).

## Apply paths (CRITICAL)
- Naukri Quick Apply when it submits on Naukri.
- If "On company site" / Workday / Greenhouse / Lever / SmartRecruiters / SuccessFactors / etc.: OPEN and COMPLETE with Rafi_Resume.docx + 52/65/immediate/Hyd. Log each redirect URL + outcome.
- Cap CAPTCHA/login walls ~3–4 min → blocked → continue.
- After apply, attempt contact recruiter / chat with 15–20 min screen ask.

## Location HARD
Hyd/Telangana OR Remote/WFH only.

## Report
1) Profile resume refresh: ok/fail + updateOn text + resume filename shown
2) Every job submit: company, role, id/URL, location, Naukri vs ATS path, resume file used
Counts: profileUpdated / applied / external / blocked / skipped
```
