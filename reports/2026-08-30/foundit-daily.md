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
- **NeuraFlash / AWS Solution Architect**: Hi — I'm applying for AWS Solution Architect at NeuraFlash. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed (rafi.success@gmail.com / +91 8790251698)
- **fetchjobs.co / Software Development Manager**: Hi — I'm applying for Software Development Manager at fetchjobs.co. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed (rafi.success@gmail.com / +91 8790251698)
- **Jobgether / Engineering Manager, AI Product Development**: Hi — I'm applying for Engineering Manager, AI Product Development at Jobgether. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed (rafi.success@gmail.com / +91 8790251698)

## Notes
- 4× `linkedin_no_easy_apply` after Falcon `APPLY_REDIRECT_STAGE_ONE` correctly recorded as `external_ats_incomplete` (Applied-tab +4 noise only).
- Filter miss: Jobgether **Engineering Manager, AI Product Development** passed via Arch/Lead EM exception — fix in filters.js (pure AI: `engineering manager, AI` / `AI product`).
- Artifact: `/opt/cursor/artifacts/foundit-apply-report.json` (ts=2026-08-30T03:47:36.805Z)

## Post-fix re-run (#289)
- Applied tab: **452 → 452** (+0). Intentional logged: **0**.
- Jobgether Engineering Manager, AI Product Development correctly skipped (`pure AI/data without .NET on title`).
- Skips: 1200 | duplicates: 68 | blocked: 0.
