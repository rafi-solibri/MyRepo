# Instahyre — issues & fixes

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
