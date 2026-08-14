# Notification — issues & fixes

Portal-scoped log. Each daily agent (cloud or home) must append **only** to this file via
`bash scripts/append-issue-fix.sh notification "issue" "fix"` — never edit `ISSUES_AND_FIXES.md` for same-day rows.

## 2026-08-14 (cloud)

| Issue | Fix |
| --- | --- |
| shared ISSUES_AND_FIXES.md parallel squash left conflict markers on main | per-portal automation-prompts/issues/<portal>.md + append-issue-fix.sh + assert-no-conflict-markers in auto-merge |
