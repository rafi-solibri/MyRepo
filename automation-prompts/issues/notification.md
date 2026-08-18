# Notification — issues & fixes

## 2026-08-18 (cloud)

| Issue | Fix |
| --- | --- |
| Ensure Missing Cursor Automation cannot be created via API; 9 AM cron misses had no mid-morning recovery | Added GitHub Actions workflow Ensure Missing Daily Runs (cron 0 5 * * * = 10:30 IST) calling ensure-missing-daily-runs.sh; docs updated; owner still pastes Cursor Automation once |
| 9 AM apply crons enabled but fired zero agents 2026-08-18; Ensure Missing automation absent; Notification only reported 0 applies | Notification prompt now runs ensure-missing-daily-runs.sh on cron miss; rerun-daily-after-fix --portal is exclusive (no longer also re-launches tip-of-main portal e.g. linkedin) |


## 2026-08-15 (home)

| Issue | Fix |
| --- | --- |
| portal-home-daily republished prior-day JSON over same-day results (Foundit/Instahyre wiped) | prefer same-day report or write stub; publish-home-result refuses stale date unless HOME_PUBLISH_ALLOW_STALE=1 |


Portal-scoped log. Each daily agent (cloud or home) must append **only** to this file via
`bash scripts/append-issue-fix.sh notification "issue" "fix"` — never edit `ISSUES_AND_FIXES.md` for same-day rows.

## 2026-08-14 (cloud)

| Issue | Fix |
| --- | --- |
| auto-merge post-fix re-run skipped because gh pr view used deleted branch | Query merge state via PR URL after squash --delete-branch |
| shared ISSUES_AND_FIXES.md parallel squash left conflict markers on main | per-portal automation-prompts/issues/<portal>.md + append-issue-fix.sh + assert-no-conflict-markers in auto-merge |
