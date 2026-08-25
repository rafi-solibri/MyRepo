# Naukri daily — 2026-08-25 (post-fix re-run #1)

Same-day re-run after merged `#257` (`POST_FIX_RERUN=1`). Ran on `main` `c507fd2` then applied with `node tools/naukri/daily_apply.js`. Do not invent applies.

## Summary
- Profile resume refresh (STEP 0, old helper): **fail** (`updated_today_unconfirmed`, still `Uploaded on 24/08/2026`, filename `Mohammed_Abdul_Rafi_Ahmed_Resume.docx`)
- Profile resume after TopTier helper fix (mid-run tailor + restore): **ok** — `Rafi_Resume.docx`, **Uploaded today**
- Applied this session: **8** (all Naukri Quick Apply, all JD-tailored `Rafi_Resume.docx`)
- External / company-site completed: **0**
- Blocked: **8** · Skipped: **739** · Seen: **130**
- Counts: profileUpdated=false (STEP 0) / applied=8 / external=0 / blocked=8 / skipped=739

## Profile resume
- Canonical file: `resumes/Rafi_Resume.docx`
- STEP 0 used legacy `setInputFiles` + `button:has-text('Update')` (re-opens picker). UI stayed `Uploaded on 24/08/2026`.
- Live TopTier widget is `#profile-section-resume` + hidden `input#resume`. Fix: filechooser on **Update**, do not re-click Update as Save, match IST `Uploaded on DD/MM/YYYY` / `Uploaded today`.
- Mid-run proof (`/tmp/naukri-tailored-profile-upload.json`): `uploadedVia: toptier-filechooser`, `profileUpdated: true`, `verify.updateOn: Uploaded today`.
- End-of-run restore to canonical CV: **ok**.

## Applied (Naukri Quick Apply, tailored Rafi_Resume.docx)
- Tech Mahindra — Technical Architect (Cloud & Microservices) — Hyderabad, Pune, Bengaluru — [listing](https://www.naukri.com/job-listings-technical-architect-cloud-microservices-tech-mahindra-hyderabad-pune-bengaluru-10-to-20-years-240826002641?src=directSearch) — `chatbot:responses_thanks`
- HYLAND — Senior Software Architect — Hyderabad — [listing](https://www.naukri.com/job-listings-senior-software-architect-hyland-hyderabad-10-to-15-years-240826018624?src=directSearch) — `chatbot:responses_thanks`
- Tata Consultancy Services — Integration Consultant / Enterprise Integration Architect — Hyderabad, Pune, Bengaluru — [listing](https://www.naukri.com/job-listings-integration-consultant-enterprise-integration-architect-tata-consultancy-services-hyderabad-pune-bengaluru-10-to-17-years-240826006187?src=directSearch) — `chatbot:responses_thanks`
- Sonata Software — AWS Data Migration Architect — Hybrid Hyderabad/Chennai/Bengaluru — [listing](https://www.naukri.com/job-listings-aws-data-migration-architect-sonata-software-hyderabad-chennai-bengaluru-10-to-20-years-240826026002?src=directSearch) — CTA recorded `view_applied_jobs` (weaker confirm)
- Big 4 Accounting Firms (Anlage Infotech) — Dotnet Full stack with AI Manager — Hybrid Hyderabad/Bengaluru — [listing](https://www.naukri.com/job-listings-dotnet-full-stack-with-ai-manager-anlage-infotech-hyderabad-bengaluru-10-to-13-years-240826001851?src=directSearch) — `chatbot:responses_thanks`
- Consulting Firm (Anlage Infotech) — .Net Azure AI Manager Professionals — Hybrid Hyderabad/Bengaluru — [listing](https://www.naukri.com/job-listings-net-azure-ai-manager-professionals-anlage-infotech-hyderabad-bengaluru-10-to-13-years-250826006496?src=directSearch) — CTA recorded `view_applied_jobs` (weaker confirm)
- Tiger Analytics — Principal Engineer — Hybrid Hyderabad/Chennai/Bengaluru — [listing](https://www.naukri.com/job-listings-principal-engineer-tiger-analytics-hyderabad-chennai-bengaluru-12-to-18-years-240826003333?src=directSearch) — `chatbot:responses_thanks`
- Everestdx — Azure Cloud Architect — Hyderabad, Chennai — [listing](https://www.naukri.com/job-listings-azure-cloud-architect-everestdx-hyderabad-chennai-8-to-12-years-200826027021?src=directSearch) — `chatbot:responses_thanks`

## Already applied earlier (skipped, not re-counted)
- Capco — GCP Tech Lead — detail CTA `Applied`

## Blocked
- Nagarro — Principal Engineer (IT Capability & Maturity Assessment) — SmartRecruiters `external_incomplete_or_timeout`
- Optum / UnitedHealth Group — Architect — cookie + Candidate Experience Survey (`Not Now`) — `external_incomplete_or_timeout` (overlay dismiss patched for next run)
- Tata Consultancy Services — Aws Solution Architect — Naukri `apply_unconfirmed`
- Experian — Solutions Architect — SmartRecruiters `external_incomplete_or_timeout`
- Pepsico — Mobile development - Assoc Principal Engineer — Naukri `apply_unconfirmed`
- Progress Software — Principal Rust Engineer – Language Runtime — Naukri `apply_unconfirmed`
- Accenture — Cloud Platform Architect — B2C login wall `external_incomplete_or_timeout`
- Accenture — Technology Architect — B2C login wall `external_incomplete_or_timeout`

## Code fixes this run
- `tools/naukri/update_profile_resume.js` — TopTier `#resume` filechooser + IST `Uploaded on DD/MM/YYYY`
- `tools/ats/complete_page.js` — dismiss cookie Accept + survey Not Now before company-site Apply

## Artifacts
- `/opt/cursor/artifacts/naukri-daily-apply.json`
- `reports/2026-08-25/naukri-daily-apply.json`
- `/opt/cursor/artifacts/naukri-resume-uploaded-today.png`
