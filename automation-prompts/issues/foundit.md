# Foundit — issues & fixes

## 15 Aug 2026 (cloud)

| Issue | Fix |
| --- | --- |
| Extra-query wave treated country-only Singapore/Thailand as remote via JD WFH copy; applied Jacobs Principal Electrical Engineer | hasSpecificPlace for non-India country-only cards; skip electrical/civil/mechanical titles without software/.NET on title |
| Primary .NET-token Raven queries exhausted (0 new applies, 42 duplicates); Hyd Arch/Lead/cloud inventory only appeared on Naukri-parity queries; underscore titles hid seniority; Salesforce-in-skills CPQ passed as Arch | EXTRA_QUERIES wave when applies<8; titleForMatch for _/\|; Dot Net proof; skip Salesforce-primary skills without .NET on title |


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
