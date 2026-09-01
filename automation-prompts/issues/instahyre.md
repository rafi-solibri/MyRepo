# Instahyre — issues & fixes

## 2026-09-01 (cloud)

| Issue | Fix |
| --- | --- |
| CDP launch skipped live login waiters for non-LinkedIn portals | launch-chrome-cdp live check for instahyre waiter; fail closed when CDP_REQUIRE_LIVE_LOGIN=1 |


## 2026-08-25 (cloud)

| Issue | Fix |
| --- | --- |
| preflight sync-chrome-sessions.sh unbound DESTS[$i] (PORTALS had hirist+linkedin_alt but DESTS/COOKIE_SETS/REQUIRED omitted hirist) | Insert hirist dest (/home/ubuntu/chrome-hirist-profile), cookie token, REQUIRED=1 before linkedin_alt so arrays stay aligned under set -u |


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
| Platform Architect - Java (and other Architect/Lead+Java titles) passed skipReason and got applied | java_primary hard-skip whenever Java is in the title without .NET on the title (seniority alone no longer exempts); check before generic_engineering; + tests |


## 2026-08-22 (cloud)

| Issue | Fix |
| --- | --- |
| Data Architect titles (e.g. Data Architect - AWS) passed skipReason and got applied | Add data architect to pure_ai_data_without_dotnet hard-skip in filters.js (+ test) |


## 2026-08-20 (cloud)

| Issue | Fix |
| --- | --- |
| Instahyre interest-only apply attached no JD-tailored resume; recruiters/ATS saw generic profile CV and AI screens rejected | Add tools/resume_tailor.js + update_profile_resume.js; daily_apply uploads JD-tailored headline/summary/skills to #resume-input before each interest and uses same file on company ATS |


## 2026-08-15 (home)

| Issue | Fix |
| --- | --- |
| pages()[0] foreign tab ERR_ABORT / false instahyre_login_required on home CDP | always context.newPage() in daily_apply.js and wait_for_cdp_login.js |


## 2026-08-15 (cloud)

| Issue | Fix |
| --- | --- |
| daily_apply connectOverCDP ECONNREFUSED because autofix runner never launched Chrome after preflight | run-portal-with-autofix.sh launches Chrome CDP for instahyre before apply (parity with foundit/cutshort) |
| spot-check used /jobs/{id}/ which 404s | use /job-{id}/ public URLs |
| Company-site completer still treated OneClick/SSO as fillable forms | complete_page.js fail-fast SSO/OneClick and prefer guest Apply |
| external_ats_detected logged but company-site never completed | Follow ATS href via tools/ats/complete_page.js |


## 2026-08-14 (cloud)

| Issue | Fix |
| --- | --- |
| CDP closed mid job_search → hard crash with no report | apiGet returns browser_closed; write partial report and stop cleanly |


Portal-scoped log. Each daily agent (cloud or home) must append **only** to this file via
`bash scripts/append-issue-fix.sh instahyre "issue" "fix"` — never edit `ISSUES_AND_FIXES.md` for same-day rows.

_No entries yet for this portal on the new per-portal log._
