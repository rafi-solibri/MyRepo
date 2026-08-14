# LinkedIn — issues & fixes

## 2026-08-14 (cloud)

| Issue | Fix |
| --- | --- |
| Easy Apply batch crashed on Page.reload ERR_ABORTED/detached frame; Interior Architect and Snowflake titles false-applied | Guard search reload/card-count; retry HTTP 999 5x; skip interior/landscape architect, Snowflake architect, Kerala city |


Portal-scoped log. Each daily agent (cloud or home) must append **only** to this file via
`bash scripts/append-issue-fix.sh linkedin "issue" "fix"` — never edit `ISSUES_AND_FIXES.md` for same-day rows.

_No entries yet for this portal on the new per-portal log._
