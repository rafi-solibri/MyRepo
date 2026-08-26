# Foundit — issues & fixes

## 2026-08-26 (cloud)

| Issue | Fix |
| --- | --- |
| Capgemini SAPBTP redirect + Manufacturing Engineering Manager passed classifyJob (skills laundry .NET / EM Arch exception) | filters.js: SAPBTP redirect requires .NET on TITLE only; skip Manufacturing/Operations Engineering Manager + manufacturing keyword without .NET on title |


## 2026-08-25 (cloud)

| Issue | Fix |
| --- | --- |
| False applies: Solutions Architect - AI, UI React/Angular Architect, Asterisk/Telephony Lead via Arch/Lead | filters.js: Instahyre-parity Architect-AI + Asterisk/telephony + UI React/Angular title skips (+ tests) |


## 2026-08-24 (cloud)

| Issue | Fix |
| --- | --- |
| Owner refreshed master resume Mohammed_Abdul_Rafi_Ahmed_Resume.docx (2026-08-24) | Replaced master + Rafi_Resume.docx alias; JD tailor still on top; upload label stays Rafi_Resume |
| Owner refreshed master resume Mohammed_Abdul_Rafi_Ahmed_Resume.docx (2026-08-23 late) | Replaced master + Rafi_Resume.docx alias (~3.9MB); JD tailor still on top; upload label stays Rafi_Resume |
| Owner refreshed master resume Mohammed_Abdul_Rafi_Ahmed_Resume.docx (2026-08-23 evening) | Replaced resumes/Mohammed_Abdul_Rafi_Ahmed_Resume.docx + Rafi_Resume.docx alias; JD tailor still runs on top; upload filename stays Rafi_Resume |


## 2026-08-23 (cloud)

| Issue | Fix |
| --- | --- |
| Owner supplied new master resume Mohammed_Abdul_Rafi_Ahmed_Resume.docx | Synced into resumes/Rafi_Resume.docx (+ Architect alias); bootstrap prefers owner-named file; JD tailor still runs on top; upload filename/label stays Rafi_Resume |
| Guidewire Technical Lead passed Arch/Lead (Duck Creek skipped; Guidewire missing) | skipTitleReason: Guidewire title parity with Naukri/LinkedIn/Instahyre |


## 2026-08-22 (cloud)

| Issue | Fix |
| --- | --- |
| Arch/Lead exception applied to Python EM / C Plus Arch / Capgemini SAPBTP Principal (false applies 2026-08-22) | Naukri NON_DOTNET_PRIMARY_RE parity on title + SAPBTP redirectUrl SAP signal in filters.js classifyJob |


## 2026-08-20 (cloud)

| Issue | Fix |
| --- | --- |
| Applies used one generic resume — ATS/AI screening rejected despite volume | Add tools/resume_tailor (+ Foundit update_profile_resume); daily_apply JD-tailors and uploads profile resume before Falcon/ATS |
| False apply: Socnet Senior Technical Lead - Agentic AI / Generative AI passed Arch/Lead without .NET on title | Expand pure AI/data title skip in tools/foundit/filters.js for agentic/generative AI (+ test); Arch/Lead exception no longer applies |


## 2026-08-16 (cloud)

| Issue | Fix |
| --- | --- |
| daily_apply.js hung after writing report (CDP WS keeps Node event loop alive; auto-merge waited 11+ min) | process.exit(0) after successful report write/console.log so cron and post-fix wrappers return |
| Snowflake Solutions Architect (INFOTRON 62845849) passed via Arch/Lead without .NET — data-platform false apply | filters.js skipTitleReason: hard-skip snowflake\|databricks titles without .NET on title (Oracle Fusion parity); filters.test.js 26.1/26.2 |


## 2026-08-15 (home)

| Issue | Fix |
| --- | --- |
| Parallel home portals taskkill shared system Chrome mid-run; apiFetch still called context.cookies and aborted | Cache Cookie header after login; Raven/Falcon continue cookie-only; soft-skip applied-count/ATS when CDP dies |
| Windows home: page.evaluate Raven search killed CDP Chrome; confirmLogin false-failed on Hi Seeker despite MSSOAT; browser.close killed shared Chrome; launch --disable-gpu / short CDP wait | apiFetch via cookies for Raven/Falcon; accept MSSOAT+onApp login; never browser.close over CDP; skip --disable-gpu on Windows launch; wait 45s for CDP |


## 2026-08-15 (cloud)

| Issue | Fix |
| --- | --- |
| daily_apply connectOverCDP ECONNREFUSED when Chrome was not launched after preflight | run-portal-with-autofix launches Chrome CDP for foundit/cutshort/instahyre before apply |
| Thailand/Singapore country-only inherited JD remote-first; underscore titles; SF-in-skills | hasSpecificPlace for non-India country; titleForMatch; Salesforce-in-skills without .NET on title |
| Engineering Manager Water and AI Specialist Solution Architect still applied after first filter pass | skip water/wastewater titles; AI Specialist Solution Architect in pure-AI skip |
| EXTRA_QUERIES Arch/Lead wave applied Facilities/Electrical/Mechanical/Oracle Fusion/AI Solution/Data Engineering titles | skipTitleReason: non-software engineering, ops EM, Oracle Fusion/ERP, AI Solution Architect, data engineering (Naukri parity) |
| .NET-only Raven queries already Applied so 0 new company-site inventory | EXTRA_QUERIES Arch/Lead wave always searched; completeExternalPage fail-fast no_ats_form |
| Generic ATS loop timed out (ats_incomplete_or_cap) and Workday maintenance burned 6.5m | Use shared completeExternalPage; fail-fast job_unavailable on community.workday.com/maintenance |
| Workday Create Account treated as ats_login_wall (Aveva etc.) so 0 company-site completes | Reuse naukri completeWorkdayApply; 6.5m cap; fillCommonAtsQuestions on generic ATS |


## 2026-08-14 (home)

| Issue | Fix |
| --- | --- |
| Applied Senior IT Analyst (Infrastructure) at NUS — .NET only in skills laundry list passed hasDotNet | skipTitleReason: infrastructure/IT analyst/sysadmin/SRE without .NET on TITLE (mirror pure-AI title rule) |


Portal-scoped log. Each daily agent (cloud or home) must append **only** to this file via
`bash scripts/append-issue-fix.sh foundit "issue" "fix"` — never edit `ISSUES_AND_FIXES.md` for same-day rows.

## 2026-08-14 (cloud cron)

| Issue | Fix |
| --- | --- |
| Applied Salesforce **Agentforce** Success Architect (Hyd) — title skip only matched `\bsalesforce\b`, and .NET in skills laundry list passed `hasDotNet` | Expand title skip to `salesforce|agentforce|sfdc`; hard-skip Salesforce employer when .NET is absent from the **title** (mirror pure-AI title rule) |
