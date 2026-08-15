# Foundit — issues & fixes

## 2026-08-15 (cloud)

| Issue | Fix |
| --- | --- |
| Generic ATS loop timed out (ats_incomplete_or_cap) and Workday maintenance burned 6.5m | Use shared completeExternalPage; fail-fast job_unavailable on community.workday.com/maintenance |
| Workday Create Account treated as ats_login_wall (Aveva etc.) so 0 company-site completes | Reuse naukri completeWorkdayApply; 6.5m cap; fillCommonAtsQuestions on generic ATS |


## 2026-08-14 (home)

| Issue | Fix |
| --- | --- |
| Applied Senior IT Analyst (Infrastructure) at NUS — .NET only in skills laundry list passed hasDotNet | skipTitleReason: infrastructure/IT analyst/sysadmin/SRE without .NET on TITLE (mirror pure-AI title rule) |


Portal-scoped log. Each daily agent (cloud or home) must append **only** to this file via
`bash scripts/append-issue-fix.sh foundit "issue" "fix"` — never edit `ISSUES_AND_FIXES.md` for same-day rows.

## 2026-08-14 (cloud cron)

| Issue | Fix |
| --- | --- |
| Applied Salesforce **Agentforce** Success Architect (Hyd) — title skip only matched `\bsalesforce\b`, and .NET in skills laundry list passed `hasDotNet` | Expand title skip to `salesforce|agentforce|sfdc`; hard-skip Salesforce employer when .NET is absent from the **title** (mirror pure-AI title rule) |
