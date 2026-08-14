# Cutshort — issues & fixes

## 2026-08-14 (cloud)

| Issue | Fix |
| --- | --- |
| FORCE_RESTORE_SESSIONS=1 overwrote live Cutshort auth with stale Aug-6 seed → login_required | ensure-missing defaults FORCE_RESTORE=0; only restore when dest missing auth |
| 0 qualifying after 1100+ scan (India-only .NET/senior cards dropped; exp max 7 for .NET) | Treat India-only senior/.NET as Hyd/remote bias; allow .NET tier2 at maxExp>=6; pull remote_okay pages; log skipReasons |
| CDP page closed during final questionnaire audit → hard exit 1 after scan | Catch TargetClosedError; still write cutshort-daily.md/stats + exit 0 path |


Portal-scoped log. Each daily agent (cloud or home) must append **only** to this file via
`bash scripts/append-issue-fix.sh cutshort "issue" "fix"` — never edit `ISSUES_AND_FIXES.md` for same-day rows.

_No entries yet for this portal on the new per-portal log._
