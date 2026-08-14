# Cutshort — issues & fixes

## 2026-08-14 (cloud)

| Issue | Fix |
| --- | --- |
| CDP page closed during final questionnaire audit → hard exit 1 after scan | Catch TargetClosedError; still write cutshort-daily.md/stats + exit 0 path |


Portal-scoped log. Each daily agent (cloud or home) must append **only** to this file via
`bash scripts/append-issue-fix.sh cutshort "issue" "fix"` — never edit `ISSUES_AND_FIXES.md` for same-day rows.

_No entries yet for this portal on the new per-portal log._
