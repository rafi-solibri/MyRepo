# Foundit daily — 2026-08-15 (post-fix re-run after #163)

## Summary
- Login: **Hi, Rafi Ahmed Mohammed Abdul** (MSSOAT / JWT OK; dashboard confirmed)
- Resume: `resumes/Rafi_Resume.docx` (never invented; no Architect stub required)
- This re-run Applied tab: **457 → 457** (+0)
- Intentional applies this session: **0** (do not invent applies)
- Duplicates skipped via `userJobInfo`: **43**
- Filter skips: **496**
- Blocked: **0**
- Age window expanded through 3650d; candidates: d1=35, d3=46, d7=74, d14=125, d30=135, d90=110, d3650=14
- Head: `3fc57c3` — `fix(ats): use the one env password for every Workday/ATS helper` (#163)
- Artifact: `/opt/cursor/artifacts/foundit-apply-report.json`
- No `canJobApply` dry-run calls
- ATS secrets present this session (`NAUKRI_WORKDAY_PASSWORD` aliased to `WORKDAY_PASSWORD` / `ATS_PASSWORD`; `LINKEDIN_EMAIL` aliased to `APPLY_EMAIL`)

## Why +0 on this re-run
Eligible Hyd/remote .NET Architect / Lead / EM inventory was already on the Applied tab from today's earlier Foundit runs (original daily + prior post-fix re-runs). `daily_apply.js` skipped those as `userJobInfo` duplicates. No leftover Workday/company-site ATS cards remained for #163 to complete with the shared password alias — Aveva / prior ATS hops were already registered on Foundit.

## Applied this session
None.

## Already applied today (skipped, not re-submitted)
`userJobInfo` duplicates this pass (43):
- Kumaran Systems — Lead .Net Developer
- ST Logistics — Manager - IT (Solution Architect) - ref D
- infomatix web technologies llp — Senior .NET Full Stack Engineer
- ST Logistics — Manager - IT (Solution Architect)
- Mphasis — Senior Software Engineer
- Tata Consultancy Services — Dot NET Full Stack Lead
- Concentrix — Engineering Manager
- Closeloop Technologies — Web Engineering Manager
- Sprinto — Senior Staff Engineer
- embrace software inc — Lead Engineer/ Architect (.NET) - Industrial
- relq technologies — Senior .NET Full Stack Developer- India
- Infosys — .Net production support Lead
- Microsoft Corp — Principal Consultant - Dotnet Full stack & AI
- Coupa Software — Sr Lead Software Engineer - Full Stack (.NET with React)
- NeuraFlash — Sr. AWS Developer
- Accenture — Technology Architect (×2)
- VeriPark — Software Development Manager
- Aveva / AVEVA — Senior/Principal Consultant - System Platform (×3), R&D Principal Technologist
- Hyland — Senior Software Architect - .NET
- Persistent Systems — .NET Lead
- Beghou Consulting — Team Lead - Enterprise .NET Developer
- Kumaran Systems — Technical Lead .NET Full Stack
- teamified — AI Principal Engineer
- Sonata Software — CE Architect with AI Expertise
- Techno-comp — .Net Architect
- Spectrum Consultants — Senior Principal .Net Architect - MedTech
- wonderbiz — .Net Full Stack Technical Lead
- Cimpress — Lead Software Engineer(.Net)-Remote
- 3Pillar Global — Technical lead - Fullstack (.Net & ReactJS)
- ValueMomentum — Sr. Full stack .NET Developer/ Tech Lead
- ********** — Technical Solution Architect
- SimCorp — Principal AI & Full Stack Software Engineer; Principal Software Engineer (Azure, .Net and Angular)
- Deltek — Accounts Manager (Principal Sales Rep)
- Cubic Transportation Systems — Principal Software Engineer (.Net)
- programmers.io — Solutions Architect
- Credence HR Services — Director Agentic AI & Enterprise Transformation
- The Wells Fargo Foundation — Principal Engineer - .NET Core / GenAI
- Jobgether — Senior Azure AppDev Architect (Remote)

## Top skip reasons
- location not Hyd/remote: 195
- no .NET on title+skills: 137
- no seniority keyword on title: 105
- junior/mid maxExp bands: 39
- listed max CTC under 35 LPA: 8
- WPF/hardware desktop: 4
- SAP without .NET: 3
- PM/TPM/delivery: 2
- Salesforce / infra-ops / pure AI without .NET on title: 3

## LinkedIn referral drafts
None this re-run (0 new applies).

## Auto-fix
No new code-fixable blocker. Did not launch another post-fix re-run (already inside `POST_FIX_RERUN=1`; this is the 5th Foundit post-fix re-run today, cap 5).
