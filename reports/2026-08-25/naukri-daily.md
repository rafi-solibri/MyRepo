# Naukri daily — 2026-08-25 (post-fix re-run #3, merged `#263`)

`POST_FIX_RERUN=1`. Date=2026-08-25 IST.

Checked out `main` `041cecc` (`fix(naukri): always rebuild Rafi_Resume from owner master (#263)`), then ran `bash scripts/preflight-portal-run.sh naukri`, `bash scripts/launch-chrome-cdp.sh naukri`, and `node tools/naukri/daily_apply.js`. Do not invent applies. Skip jobs already applied today.

This is the same-day re-run so today's applies/email use the merged helper. Earlier morning/post-fix sessions did **not** apply with `#263`.

## Summary
- Profile resume refresh (STEP 0, merged helper): **ok** — `Rafi_Resume.docx` rebuilt from `Mohammed_Abdul_Rafi_Ahmed_Resume.docx` (3957700 → 20945 bytes, matching text SHA `403c6a36869581a9`), **Uploaded today**, `profileUpdated: true` on first attempt (`toptier-filechooser`)
- Applied this session: **6** (all Naukri Quick Apply, all JD-tailored `Rafi_Resume.docx`)
- External / company-site completed: **0**
- Blocked: **4** · Skipped: **2855** · Seen: **263**
- Counts: profileUpdated=true / applied=6 / external=0 / blocked=4 / skipped=2855
- End-of-run profile restore to canonical CV: **ok** (`Rafi_Resume.docx`, still Uploaded today)
- Expanded ages: 1 then 3,7 then 15,30,60 + extra .NET/Azure queries + recommended/homepage

## Profile resume (STEP 0)
- Owner master: `resumes/Mohammed_Abdul_Rafi_Ahmed_Resume.docx`
- Upload copy: `resumes/Rafi_Resume.docx` (always rebuilt by `#263` `ensure_upload_resume.py`)
- Artifact: `/opt/cursor/artifacts/naukri-profile-resume.json`
- `verify.matchedToken`: Uploaded today
- `verify.resumeName`: Resume / Update / Rafi_Resume.docx / Uploaded today
- Login: Naukri cookies present (`nauk_rt` / `nauk_at`); profile shows Mohammed Abdul Rafi Ahmed
- Screenshot: `/opt/cursor/artifacts/naukri-profile-uploaded-today-rerun3.png`

## Applied this session (Naukri Quick Apply, tailored `Rafi_Resume.docx`)
- TeizoSoft (listed as Hiring for an IT Services & Consulting company) — Snowflake - Lead Development Engineer — Hybrid Hyderabad — [listing](https://www.naukri.com/job-listings-snowflake-lead-development-engineer-teizosoft-hyderabad-8-to-13-years-250826009170?src=directSearch) — `chatbot:responses_thanks`
- Innova Solutions — Senior .NET Engineer — Hybrid Hyderabad/Noida/Bengaluru — [listing](https://www.naukri.com/job-listings-senior-net-engineer-innova-solutions-noida-hyderabad-bengaluru-7-to-12-years-280726031544?src=directSearch) — CTA recorded `view_applied_jobs` (weaker confirm)
- Michael Page (Leading Consumer Products GCC) — Cloud Architect — Hyderabad — [listing](https://www.naukri.com/job-listings-cloud-architect-michael-page-hyderabad-9-to-13-years-290726034841?src=directSearch) — `chatbot:responses_thanks`
- Presidio Solutions — Cloud Migration Associate Architect — Hyderabad/Chennai/Bengaluru — [listing](https://www.naukri.com/job-listings-cloud-migration-associate-architect-presidio-solutions-hyderabad-chennai-bengaluru-10-to-12-years-290726015677?src=directSearch) — `chatbot:responses_thanks`
- Centroid — OCI Cloud Architect — Remote — [listing](https://www.naukri.com/job-listings-oci-cloud-architect-centroid-hyderabad-10-to-15-years-030626010598?src=directSearch) — `chatbot:responses_thanks`
- Xtrm India — Azure Solution Architect — Remote — [listing](https://www.naukri.com/job-listings-azure-solution-architect-xtrm-india-chennai-10-to-20-years-170226024718?src=drecomm_dashboard_aurus) — `chatbot:responses_thanks`

## Already applied earlier today (not re-counted)
From post-fix re-run #1 (`bc-30ec03be`, report on `cursor/naukri-daily-post-fix-re-run-2026-08-25-9d86`):
- Tech Mahindra — Technical Architect (Cloud & Microservices)
- HYLAND — Senior Software Architect
- Tata Consultancy Services — Integration Consultant / Enterprise Integration Architect
- Sonata Software — AWS Data Migration Architect
- Big 4 Accounting Firms (Anlage Infotech) — Dotnet Full stack with AI Manager
- Consulting Firm (Anlage Infotech) — .Net Azure AI Manager Professionals
- Tiger Analytics — Principal Engineer
- Everestdx — Azure Cloud Architect

This session also skipped:
- Clean Harbors — .Net Fullstack Tech Lead (`already_applied_detail`)

## Blocked this session
- Qualcomm — Cloud Platform Development Engineer -Staff — Hyderabad/Bengaluru — company ATS login wall (`ats_login_wall`) — https://careers.qualcomm.com/careers/apply?pid=446720272187
- Wells Fargo — Principal Engineer — Hyderabad — Workday login wall (`ats_login_wall`) — https://wd1.myworkdaysite.com/en-US/recruiting/wf/WellsFargoJobs/job/Hyderabad%2C-India/Principal-Engineer_R-568420/apply/applyManually
- Qualcomm — Principal Engineer - Core Platform Storage — Hyderabad — company ATS login wall — https://careers.qualcomm.com/careers/apply?pid=446717672570
- Qualcomm — Principal Engineer- Camera — Hyderabad — company ATS login wall — https://careers.qualcomm.com/careers/apply?pid=446717554986

Hirist login walls skipped (not hard-blocked): 3 (`hirist_login_required_skip`).

## Other skips of note
Top skip reasons: duplicate_in_run 2583 · skip_title_keyword 177 · skip_no_dotnet 34 · skip_seniority 29 · skip_company 13 · skip_ctc_max_30 6 · skip_location 6

## Email
- Resend MCP: first send to the work inbox from `onboarding@resend.dev` was rejected (test sender can only mail the Resend account owner).
- Retry to the Resend account owner inbox succeeded — id `9dbe5b2c-e37d-4a54-85bb-de7108cfb155`. Set `RESEND_FROM_EMAIL` on a verified domain to mail the work inbox.
- Notification Job 11 AM is the all-portal digest.

## Code fix
None this session. `#263` already on `main` and used for STEP 0 + applies (resume always rebuilt from owner master). No new code-fixable blocker; no additional post-fix re-run launched (this is re-run 3 of 5 for Naukri on 2026-08-25 IST).

## Artifacts
- `/opt/cursor/artifacts/naukri-profile-resume.json`
- `/opt/cursor/artifacts/naukri-daily-apply.json`
- `/opt/cursor/artifacts/naukri-profile-uploaded-today-rerun3.png`
- `/opt/cursor/artifacts/naukri-profile-after-restore-rerun3.png`
- `reports/2026-08-25/naukri-daily.md`
- `reports/2026-08-25/naukri-daily-run.json`
- `reports/2026-08-25/naukri-profile-resume.json`
