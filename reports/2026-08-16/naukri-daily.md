# Naukri daily — 2026-08-16 (post-fix re-run on merged main)

Automation: https://cursor.com/automations/003b88eb-909a-11f1-ba66-0e7d0216e441
This session: https://cursor.com/agents/bc-286477d7-d578-43d4-8a94-e246c4d74819
`POST_FIX_RERUN=1` on `39cc3e9` (`main` after #198). Earlier cron (`bc-9bfe004e`) merged #194 and did not apply with that fix.

## Summary
- Profile resume refresh: **ok** — `Rafi_Resume.docx` / “Uploaded today” (`profileUpdated: true`, `matchedToken: today`)
- Applied this session: **1**
- External / company-site completed: **0**
- Blocked: 2 · Skipped: 331 · Seen: 100
- Early expand ages 3/7 (applied &lt; 3), then 15/30/60 + extra .NET/Azure queries (applied &lt; 8)

## Applied
1. Tata Consultancy Services — Enterprise Infrastructure & Cloud Architect — Hyderabad, Chennai — Naukri chatbot (`chatbot:responses_thanks`) — `resumes/Rafi_Resume.docx`  
   https://www.naukri.com/job-listings-enterprise-infrastructure-cloud-architect-tata-consultancy-services-hyderabad-chennai-10-to-17-years-100726028857

## Blocked this session
- i2e Consulting — Solution Architect (Remote) — `quick_apply_not_found` / empty CTA. Same listing was already applied on 2026-08-15; not re-counted.
- Principal Financial Group — Associate Director - Engineering (Hyderabad) — `quick_apply_not_found` / empty CTA. Same chat/CTA wall as the morning cron and 2026-08-15 (`chat_steps_exhausted`). Not a new code-fixable inventory unlock.

## Skip mix (331)
- 212 duplicate_in_run
- 68 skip_title_keyword (Gemini/AI/SAP/Pega/Salesforce/ServiceNow/Java/cyber already filtered)
- 22 skip_seniority · 14 skip_no_dotnet · 8 skip_location
- 7 listed max CTC under 35 LPA

## Artifacts
- `/opt/cursor/artifacts/naukri-profile-resume.json`
- `/opt/cursor/artifacts/naukri-daily-apply.json`

## Auto-fix
No new durable helper change this re-run. Naukri same-day post-fix re-runs on 2026-08-16: this is #2 of 5 (prior: `bc-718d861c` after #194).
