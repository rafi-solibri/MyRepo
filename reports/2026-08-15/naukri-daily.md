# Naukri daily — 2026-08-15 (post-fix re-run on merged main)

Automation: https://cursor.com/automations/003b88eb-909a-11f1-ba66-0e7d0216e441  
Run: https://cursor.com/agents/bc-4f5acc30-4765-4da9-b739-102648cc40e9  
Code: `02e58e4` (`#169` Workday/guest career apply fix already on `main`)  
`POST_FIX_RERUN=1` · date 2026-08-15 IST

## Summary
- Profile resume refreshed: **yes** (`profileUpdated: true`, `Rafi_Resume.docx`, “Uploaded today”)
- Applied this re-run: **1** (not invented)
- External ATS completed: **0**
- Blocked: **1** · Skipped: **3372** (3161 duplicate_in_run) · Seen: **194**
- Already applied today (skipped): **2**

## STEP 0 — profile resume
- File: `/workspace/resumes/Rafi_Resume.docx`
- Upload: `input[id*='resume' i][type='file']` + Update
- Verify: `todayHit: true`, resume name shown `Rafi_Resume.docx` / “Uploaded today”
- Headline soft-touch: skipped (`headline_input_missing`) — freshness already confirmed

## Applied
- Johnson & Johnson — Manager Forward Deployed Engineer, Software Engineering — Hybrid Hyderabad — Naukri Quick Apply (`view_applied_jobs`) — [listing](https://www.naukri.com/job-listings-manager-forward-deployed-engineer-software-engineering-johnson-johnson-hyderabad-10-to-15-years-300726025627?src=directSearch) — resume `Rafi_Resume.docx`

## Already applied today (skipped)
- i2e Consulting — Solution Architect — Remote — CTA Applied
- Clean Harbors — .Net Fullstack Tech Lead — Hyderabad — CTA Applied

## Blocked
- Principal Financial Group — Associate Director - Engineering — Hyderabad — `apply_unconfirmed` (chatbot `chat_steps_exhausted`, CTA still Quick apply). Not counted as applied.

## Skip notes (no invented applies)
- Title keyword (Java / Salesforce / SAP / ServiceNow / Pega / AI-primary / cyber): 137
- No .NET on non-Arch/Lead titles: 29
- Seniority (IC / non-lead): 28
- Listed max CTC &lt; 35 LPA (Valuelabs .NET Architect 30, Incedo .Net Lead 30, Sonata Azure SA 31, etc.): 9
- Location: 6
- Fresh 1d/3d/7d inventory was thin; runner auto-expanded 15/30/60 + extra .NET/Azure queries + recommended/homepage

## Counts
profileUpdated **1** / applied **1** / external **0** / blocked **1** / skipped **3372**

No new code-fixable blocker found that would justify another same-day re-run. Artifacts: `/opt/cursor/artifacts/naukri-profile-resume.json`, `/opt/cursor/artifacts/naukri-daily-apply.json`.
