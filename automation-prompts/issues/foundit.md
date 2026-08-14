# Foundit — issues & fixes

## 2026-08-14 (cloud)

| Issue | Fix |
| --- | --- |
| Applied Deltek Accounts Manager (Principal Sales Rep) — isArchLeadTitle matched bare principal and bypassed .NET | Skip sales/account-management titles; require principal engineer\|architect\|consultant (not bare principal) for Arch/Lead .NET bypass |


Portal-scoped log. Each daily agent (cloud or home) must append **only** to this file via
`bash scripts/append-issue-fix.sh foundit "issue" "fix"` — never edit `ISSUES_AND_FIXES.md` for same-day rows.

## 2026-08-14 (cloud cron)

| Issue | Fix |
| --- | --- |
| Applied Salesforce **Agentforce** Success Architect (Hyd) — title skip only matched `\bsalesforce\b`, and .NET in skills laundry list passed `hasDotNet` | Expand title skip to `salesforce|agentforce|sfdc`; hard-skip Salesforce employer when .NET is absent from the **title** (mirror pure-AI title rule) |
