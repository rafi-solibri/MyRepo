# Foundit daily — 2026-08-17

## Summary
- Logged in: **yes** (MSSOAT + jwtOk + onApp; greeting sometimes `Hi, Seeker`)
- Resume: `resumes/Rafi_Resume.docx`
- First pass (morning cron): Applied tab **460 → 464** (+4)
- Post-fix re-run on #206 (no filter change): **464 → 464** (+0) — false-skipped Arch/Lead
- After filter fix (this session): **464 → 478** (+14). Intentional logged: **14**
- Comma-title confirmation pass: **478 → 478** (+0) — Newfold `Software Engineering, Manager` is Mumbai (correct skip)
- **Today total: 18** Foundit applies (4 morning + 14 this session)
- Filter-fix run: Skipped 1182 · Duplicates 71 · Blocked 0 · age → **3650d**
- Artifact: `/opt/cursor/artifacts/foundit-apply-report.json`
- No `canJobApply`

## Applied (morning first pass)
1. ANSR — Principal Engineer - IT Software (.Net) — `62960104` — Falcon + LinkedIn `4453078686` (`linkedin_no_easy_apply`)
2. HighLevel — Engineering Manager II - Phone Core — `62962472` — LinkedIn `4450455959` (`linkedin_no_easy_apply`)
3. skywaves rise — Technical Lead — `62954643` — Foundit Falcon (`NORMAL`)
4. Niit Technologies — TECHNICAL LEAD — `62962658` — LinkedIn `4454390356` (`linkedin_no_easy_apply`)

## Applied (filter-fix re-run — Foundit Falcon 200)
1. Microsoft Corp — Principal Group Engineering Manager — `62958607` — Hyd — LinkedIn `4454035034` (`linkedin_no_easy_apply`)
2. Flexton Inc — Solutions Architect — `62837624` — Remote — LinkedIn `4454027083` (`linkedin_no_easy_apply`)
3. Flexton Inc — Full Stack Solutions Architect — `62686683` — Remote — LinkedIn `4453106257` (`linkedin_no_easy_apply`)
4. HighRadius — Engineering Manager — `62691693` — Hyd — LinkedIn `4450454778` (`linkedin_no_easy_apply`)
5. Cotiviti — Senior Software Engineering Manager — `62822895` — Remote — LinkedIn `4445701868` (`linkedin_no_easy_apply`)
6. Google India — Software Engineering Manager, Payments Platform — `62691178` — Hyd — LinkedIn `4452383098` (`linkedin_no_easy_apply`)
7. Juniper Square — Technical Lead- Fullstack — `62831286` — Remote — LinkedIn `4451402878` (`linkedin_no_easy_apply`)
8. HighRadius — Technical Architect — `62528454` — Hyd — LinkedIn `4449564163` (`linkedin_no_easy_apply`)
9. Google India — Engineering Manager, Looker, Google Cloud — `62527276` — Hyd — LinkedIn `4451473259` (`linkedin_no_easy_apply`)
10. Accenture — Packaged/SaaS App Engineering Lead — `62049255` — Hyd — Falcon `NORMAL` + monsterindia event (`external_incomplete_or_timeout`)
11. Microsoft Corp — Principal Software Engineering Manager — `61663187` — Hyd — LinkedIn `4449493814` (`linkedin_no_easy_apply`)
12. Microsoft Corp — Principal Software Engineering Manager — `61531692` — Hyd — LinkedIn `4448186492` (`linkedin_no_easy_apply`)
13. modmed india — Senior Software Architect 2 — `58158367` — Hyd — LinkedIn `4435047960` (`linkedin_no_easy_apply`)
14. modmed india — Senior Software Architect — `51338483` — Hyd — LinkedIn `4400708113` (`linkedin_no_easy_apply`)

## Filter fix (code-fixable false skips)
Java in Raven **skills laundry lists** was treated as Java-primary, and `isArchLeadTitle` missed Naukri-parity titles (`Lead Software Engineer`, `Senior Manager`, `Software Engineering, Manager`). Those Hyd/remote Arch/Lead/EM cards never applied.

- Java-primary / Java-only = **title only**
- `isArchLeadTitle` aligned with Naukri `ARCH_LEAD_RE`
- Senior titles with empty Raven skills request JD enrich
- Commas/whitespace normalized in `titleForMatch`

## Top skip reasons (filter-fix run)
- location not Hyd/remote: 648 (Bangalore/Pune/Dubai/…)
- no .NET on title+skills: 232 (non-arch IC titles)
- no seniority keyword on title: 105
- junior/mid exp bands / SAP / pure AI-data / infra / ServiceNow

## LinkedIn referral drafts
1. **Microsoft Corp / Principal Group Engineering Manager** — Hi — I'm applying for Principal Group Engineering Manager at Microsoft Corp. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed ([REDACTED] / +91 8790251698)
2. **Flexton Inc / Solutions Architect** — Hi — I'm applying for Solutions Architect at Flexton Inc. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed ([REDACTED] / +91 8790251698)
3. **Flexton Inc / Full Stack Solutions Architect** — Hi — I'm applying for Full Stack Solutions Architect at Flexton Inc. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed ([REDACTED] / +91 8790251698)
