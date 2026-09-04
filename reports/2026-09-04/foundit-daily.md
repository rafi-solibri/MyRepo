# Foundit daily — 2026-09-04

## Summary
- Login: MSSOAT + jwtOk; onApp (greeting Hi, Seeker briefly — cookie+app accepted).
- Applied tab: **395 → 400** (+5 Falcon noise/applies). Intentional logged: **2**.
- Candidates: d1=52 / d14=259 / d3=108 / d30=301 / d3650=46 / d7=346 / d90=154
- Skips: 1197 | duplicates: 64 | blocked: 3.
- Age window used: 3650d.

## Applied (intentional)
- **EPAM** — Lead Software Engineer - .NET | path=`Foundit Falcon` falcon=`NORMAL` profileUpload=True
- **Tata Consultancy Services** — Oracle Apex Solution Architect | path=`Foundit Falcon` falcon=`NORMAL` profileUpload=True
  - **FALSE APPLY** — Oracle Apex is not .NET; filter miss → fixed in same-day PR (oracle apex / APEX Solution Architect).

## Blocked
- **integers.ai** — Senior .NET Full Stack Developer (React & AI) | external_ats_incomplete / linkedin_no_easy_apply | https://www.linkedin.com/jobs/view/4460982523/
- **relq technologies** — Sr .NET Full Stack Developer- India Remote | external_ats_incomplete / linkedin_no_easy_apply | https://www.linkedin.com/jobs/view/4461099896/
- **HighRadius** — Principal Product Solution Architect | external_ats_incomplete / linkedin_no_easy_apply | https://www.linkedin.com/jobs/view/4460644022/

## Top 3 LinkedIn referral drafts
### integers.ai — Senior .NET Full Stack Developer (React & AI)

Hi — I'm applying for Senior .NET Full Stack Developer (React & AI) at integers.ai. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed (rafi.success@gmail.com / +91 8790251698)

### relq technologies — Sr .NET Full Stack Developer- India Remote

Hi — I'm applying for Sr .NET Full Stack Developer- India Remote at relq technologies. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed (rafi.success@gmail.com / +91 8790251698)

### EPAM — Lead Software Engineer - .NET

Hi — I'm applying for Lead Software Engineer - .NET at EPAM. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed (rafi.success@gmail.com / +91 8790251698)

## Notes
- Artifact: `/opt/cursor/artifacts/foundit-apply-report.json`
- Resume: `resumes/Rafi_Resume.docx` (JD-tailored per apply + profile upload).
- Inventory: Hyd/.NET Arch-Lead still largely exhausted at 3650d; most eligible hits are LinkedIn SCRAPPING without Easy Apply or already Applied.

## Post-fix re-run (merged main a385176 / #323; Foundit Apex filter from #322)

Ran `daily_apply.js` on tip-of-main after `git fetch/checkout/pull --ff-only origin main`. Resume: `resumes/Rafi_Resume.docx`. Did not invent applies. Skipped jobs already applied today.

- Login: MSSOAT + jwtOk; onApp (greeting Hi, Seeker — cookie+app accepted).
- Applied tab: **400 → 400** (+0). Intentional logged: **0**.
- Candidates: d1=46 / d3=112 / d7=358 / d14=252 / d30=304 / d90=164 / d3650=45
- Skips: 1212 | duplicates: 69 | blocked: 0
- Age window used: 3650d
- **TCS Oracle Apex Solution Architect** (jobId 65422784) → skipped `Oracle Fusion/ERP without .NET on title` (filter from #322 held; no re-apply).
- **EPAM Lead Software Engineer - .NET** (jobId 65422797) → duplicate via `userJobInfo` (already applied this morning).
- integers.ai / relq / HighRadius LinkedIn redirects → already in Applied (`userJobInfo`); still not counted as new applies.
- No new code-fixable blocker. Inventory still exhausted at 3650d.
- Artifact: `/opt/cursor/artifacts/foundit-apply-report-postfix.json` (copy: `reports/2026-09-04/foundit-apply-report-postfix.json`)
