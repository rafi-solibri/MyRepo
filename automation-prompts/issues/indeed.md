# Indeed — issues & fixes

## 2026-08-14 (cloud)

| Issue | Fix |
| --- | --- |
| UC CF cleared but anonymous Sign-in home → 0 seen silent fail | Detect unsigned-in home after clear_cf; exit 5 with indeed_login_required |


Portal-scoped log. Each daily agent (cloud or home) must append **only** to this file via
`bash scripts/append-issue-fix.sh indeed "issue" "fix"` — never edit `ISSUES_AND_FIXES.md` for same-day rows.

_No entries yet for this portal on the new per-portal log._
