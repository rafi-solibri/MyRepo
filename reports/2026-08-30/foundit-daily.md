# Foundit daily — 2026-08-30

- Login: loggedIn=True jwtOk=True onApp=True (greeting may show Hi, Seeker briefly)
- Applied tab: **448 → 452** (+4). Intentional logged: **0**.
- Age window used: **3650d**
- Candidates: d1=65 / d3=78 / d7=263 / d14=284 / d30=333 / d90=206 / d3650=43
- Skips: 1201 | duplicates: 67 | blocked: 4

## Applied (intentional)
- _(none — do not invent applies)_

## Blocked (Falcon redirect incomplete — not counted)
- **AWS Solution Architect** @ NeuraFlash — `linkedin_no_easy_apply` (https://www.linkedin.com/jobs/view/4459104273/)
- **Software Development Manager** @ fetchjobs.co — `linkedin_no_easy_apply` (https://www.linkedin.com/jobs/view/4458548588/)
- **Engineering Manager, AI Product Development** @ Jobgether — `linkedin_no_easy_apply` (https://www.linkedin.com/jobs/view/4456859470/)
- **Lead Software Engineer, ITC** @ Nike — `linkedin_no_easy_apply` (https://www.linkedin.com/jobs/view/4458774048/)

## Top 3 LinkedIn referral drafts
- **NeuraFlash / AWS Solution Architect**: Hi — I'm applying for AWS Solution Architect at NeuraFlash. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed ([REDACTED] / +91 8790251698)
- **fetchjobs.co / Software Development Manager**: Hi — I'm applying for Software Development Manager at fetchjobs.co. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed ([REDACTED] / +91 8790251698)
- **Jobgether / Engineering Manager, AI Product Development**: Hi — I'm applying for Engineering Manager, AI Product Development at Jobgether. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed ([REDACTED] / +91 8790251698)

## Notes
- 4× `linkedin_no_easy_apply` after Falcon `APPLY_REDIRECT_STAGE_ONE` correctly recorded as `external_ats_incomplete` (Applied-tab +4 noise only).
- Filter miss: Jobgether **Engineering Manager, AI Product Development** passed via Arch/Lead EM exception — fix in filters.js (pure AI: `engineering manager, AI` / `AI product`).
- Artifact: `/opt/cursor/artifacts/foundit-apply-report.json` (ts=2026-08-30T03:47:36.805Z)

## Post-fix re-run (#289)
- Applied tab: **452 → 452** (+0). Intentional logged: **0**.
- Jobgether Engineering Manager, AI Product Development correctly skipped (`pure AI/data without .NET on title`).
- Skips: 1200 | duplicates: 68 | blocked: 0.

## Post-fix re-run (#293) — 2026-08-30 IST, `POST_FIX_RERUN=1` on `main` @ `fa8b17f`
- Login: loggedIn=True jwtOk=True onApp=True (greeting Hi, Seeker; MSSOAT + dashboard).
- Applied tab: **447 → 458** (+11). Intentional logged: **2**. Age → **3650d**.
- Candidates: d1=203 / d3=75 / d7=270 / d14=229 / d30=253 / d90=190 / d3650=42.
- Skips: 1192 | duplicates: 59 | blocked: 9.
- Resume: `resumes/Rafi_Resume.docx` + per-job tailor + profile upload (both intentional applies).
- No `canJobApply` dry-run. Already-applied today skipped via userJobInfo / applicationStatus.

### Applied (intentional — Foundit Falcon native)
- **PU1 Support- Architect - Offshore Manager** @ Capgemini — Foundit Falcon (`jobId` 64753771, next=NORMAL). **False apply** (AMS support-architect; no SAPBTP URL so prior SAP redirect skip missed).
- **Engineering Manager Mobile Application(Android /IOS)** @ right advisors private limited — Foundit Falcon (`jobId` 64686483, next=NORMAL). **False apply** (Android/iOS mobile EM; Arch/Lead waived .NET on title).

### Blocked (Falcon redirect incomplete — not counted)
- **Functional Architect (ISG)** @ Cognizant Consulting — `linkedin_no_easy_apply` (https://www.linkedin.com/jobs/view/4457489798/)
- **Solutions Architect** @ one75mb hrm pvt ltd. — `linkedin_no_easy_apply` (https://www.linkedin.com/jobs/view/4459160871/)
- **Senior Software Architect/Technical Lead** @ RevUnit — `linkedin_no_easy_apply` (https://www.linkedin.com/jobs/view/4460388916/)
- **Senior Software Architect / Technical Lead** @ RevUnit — `linkedin_no_easy_apply`
- **Engineering Manager** @ Cognizant Consulting — `linkedin_no_easy_apply`
- **Lead Principal Advanced Services Engineer** @ Oracle — `linkedin_no_easy_apply`
- **Technical Lead IFS** @ Jobgether — `linkedin_no_easy_apply`
- **Engineering Manager - Product** @ Jobgether — `linkedin_no_easy_apply`
- **Software Security Architect** @ Hyland — `linkedin_no_easy_apply`

### Top 3 LinkedIn referral drafts
- **Cognizant Consulting / Functional Architect (ISG)**: Hi — I'm applying for Functional Architect (ISG) at Cognizant Consulting. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed ([REDACTED] / +91 8790251698)
- **Capgemini / PU1 Support- Architect - Offshore Manager**: Hi — I'm applying for PU1 Support- Architect - Offshore Manager at Capgemini. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed ([REDACTED] / +91 8790251698)
- **one75mb hrm pvt ltd. / Solutions Architect**: Hi — I'm applying for Solutions Architect at one75mb hrm pvt ltd.. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed ([REDACTED] / +91 8790251698)

### False applies / code fix
- Capgemini **PU1 Support- Architect** native Falcon (no SAPBTP URL) + right advisors **Android/iOS mobile EM** passed via Arch/Lead / skills laundry .NET.
- Filter: title-only skip `support architect` / `PU1 Support` and `android|ios|mobile application` when .NET is not on the title.

Artifact: `/opt/cursor/artifacts/foundit-apply-report.json` (ts=2026-08-30T14:37:53.547Z; copy: `reports/2026-08-30/foundit-apply-report.json`)
