# Naukri — issues & fixes

## 2026-08-14 (cloud)

| Issue | Fix |
| --- | --- |
| False applies: Marketing Director, Azure AI ML Architect, Data/Oracle/Jira/Network-Security/Endpoint/Pricing architects | resume_and_filters.js: skip marketing/jira/atlassian/endpoint/pricing/process/network&security/cyber architecture; PURE_AI_DATA data architect + AI ML; NON_DOTNET oracle |
| Applied Senior Manager Attack Surface Reduction (cyber) via Senior Manager arch-lead waiver | SKIP_TITLE_RE: attack surface / cybersecurity / infosec / SOC / MDR |


Portal-scoped log. Each daily agent (cloud or home) must append **only** to this file via
`bash scripts/append-issue-fix.sh naukri "issue" "fix"` — never edit `ISSUES_AND_FIXES.md` for same-day rows.

## 2026-08-14 (cloud cron)

| Issue | Fix |
| --- | --- |
| 13× `apply_unconfirmed` with `chat_steps_exhausted` / delayed drawer (Save no-op under overlay; narrow chips) | `daily_apply.js`: Playwright force Save, stuck detection, broader chips/select/textarea answers, late thanks confirm |
| Wrong applies/attempts: Gen AI SA, Agentforce, Network Support, Civil/Structural EM, QE Architect, Data Engineering Manager | `resume_and_filters.js` + `test_filters.js`: expand `SKIP_TITLE_RE` / `PURE_AI_DATA_RE` (`gen ai`, `ai agent`, Architect…AI/ML) |
