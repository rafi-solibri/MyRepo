# Foundit — issues & fixes

## 2026-08-15 (home)

| Issue | Fix |
| --- | --- |
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
