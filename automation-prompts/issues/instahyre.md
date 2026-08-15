# Instahyre — issues & fixes

## 2026-08-15 (cloud)

| Issue | Fix |
| --- | --- |
| ATS spot-check used /jobs/{id}/ which 404s | Use /job-{id}/ (canonical slug redirect) + already-interested ATS follow-up helper |
| Company-site completer still treated OneClick/SSO as fillable forms | complete_page.js fail-fast SSO/OneClick and prefer guest Apply |
| external_ats_detected logged but company-site never completed | Follow ATS href via tools/ats/complete_page.js |


## 2026-08-14 (cloud)

| Issue | Fix |
| --- | --- |
| CDP closed mid job_search → hard crash with no report | apiGet returns browser_closed; write partial report and stop cleanly |


Portal-scoped log. Each daily agent (cloud or home) must append **only** to this file via
`bash scripts/append-issue-fix.sh instahyre "issue" "fix"` — never edit `ISSUES_AND_FIXES.md` for same-day rows.

_No entries yet for this portal on the new per-portal log._
