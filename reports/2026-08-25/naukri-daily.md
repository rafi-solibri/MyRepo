# Naukri daily — 2026-08-25 (post-fix re-run #2, merged `#261`)

`POST_FIX_RERUN=1`. Checked out `main` `5823080` (`fix(naukri): compress resume under 2MB and harden profile STEP 0 (#261)`), then ran `bash scripts/preflight-portal-run.sh naukri`, `bash scripts/launch-chrome-cdp.sh naukri`, and `node tools/naukri/daily_apply.js`. Do not invent applies. Skip jobs already applied today.

## Summary
- Profile resume refresh (STEP 0, merged helper): **ok** — `Rafi_Resume.docx` (20945 bytes), **Uploaded today**, `profileUpdated: true` on first attempt (`toptier-filechooser`)
- Applied this session: **0** (inventory already consumed by earlier same-day post-fix run; none invented)
- External / company-site completed: **0**
- Blocked: **1** · Skipped: **2633** · Seen: **203**
- Counts: profileUpdated=true / applied=0 / external=0 / blocked=1 / skipped=2633
- End-of-run profile restore to canonical CV: **ok**
- Expanded ages: 3,7 then 15,30,60 + extra .NET/Azure queries

## Profile resume (STEP 0)
- Canonical file: `resumes/Rafi_Resume.docx` (compressed under 2MB by `#261`)
- Artifact: `/opt/cursor/artifacts/naukri-profile-resume.json`
- `verify.matchedToken`: Uploaded today
- `verify.resumeName`: Resume / Update / Rafi_Resume.docx / Uploaded today
- Login: Naukri cookies present (`nauk_rt` / `nauk_at`); profile shows Mohammed Abdul Rafi Ahmed

## Applied this session
_None confirmed (no invented applies)._

## Already applied earlier today (not re-counted)
From the earlier same-day post-fix run (`bc-30ec03be`, report on `cursor/naukri-daily-post-fix-re-run-2026-08-25-9d86`):
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
- Conduent — Senior Manager, App Development & Support — Hyderabad — Naukri `apply_unconfirmed` (empty CTA after Quick Apply / `no_chat`) — [listing](https://www.naukri.com/job-listings-senior-manager-app-development-support-conduent-business-services-india-llp-hyderabad-15-to-20-years-290726909229?src=drecomm_dashboard_aurus) — tailored `Rafi_Resume.docx` synced to profile first; not counted as applied

## Other skips of note
- Hirist login wall (skipped, not hard-blocked): Rapidue Solution Architect; Mancer Engineering Manager - Platform
- Company site / no ATS form: Birlasoft Sr Technical Lead-Windchill Integration; Apple Senior Engineering Manager
- Top skip reasons: duplicate_in_run 2411 · skip_title_keyword 142 · skip_no_dotnet 34 · skip_seniority 20 · skip_company 7 · skip_ctc_max_30 5 · skip_location 5

## Email
- Resend MCP: first send to the work inbox from `onboarding@resend.dev` was rejected (test sender can only mail the Resend account owner).
- Retry to the Resend account owner inbox succeeded — id `2594367d-52e6-4e30-ba6b-d3c502e9ac1c`. Set `RESEND_FROM_EMAIL` on a verified domain to mail the work inbox.
- Notification Job 11 AM is the all-portal digest.

## Code fix
None this session. `#261` already on `main` and used for STEP 0. No new code-fixable blocker; no additional post-fix re-run launched (cap 5/portal/IST day).

## Artifacts
- `/opt/cursor/artifacts/naukri-profile-resume.json`
- `/opt/cursor/artifacts/naukri-daily-apply.json`
- `/opt/cursor/artifacts/naukri-profile-uploaded-today-postfix.png`
- `reports/2026-08-25/naukri-daily.md`
- `reports/2026-08-25/naukri-daily-run.json`
- `reports/2026-08-25/naukri-profile-resume.json`
