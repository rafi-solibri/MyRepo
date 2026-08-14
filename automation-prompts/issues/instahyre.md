# Instahyre — issues & fixes

## 2026-08-14 (cloud)

| Issue | Fix |
| --- | --- |
| enqueueJob called locationOk(location) so #151 pan-India/senior soften never ran on apply path | Pass title+skills into locationOk(location, title, skills) in daily_apply.js |
| CDP closed mid job_search → hard crash with no report | apiGet returns browser_closed; write partial report and stop cleanly |


Portal-scoped log. Each daily agent (cloud or home) must append **only** to this file via
`bash scripts/append-issue-fix.sh instahyre "issue" "fix"` — never edit `ISSUES_AND_FIXES.md` for same-day rows.

_No entries yet for this portal on the new per-portal log._
