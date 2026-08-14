# Hitech City / Knowledge City — issues & fixes

Portal-scoped log. Each daily agent (cloud or home) must append **only** to this file via
`bash scripts/append-issue-fix.sh hitechcity "issue" "fix"` — never edit `ISSUES_AND_FIXES.md` for same-day rows.

## 2026-08-14 (cloud)

| Issue | Fix |
| --- | --- |
| parallel portal PRs collided on shared issues log | portal-scoped issues/hitechcity.md only |
| Indeed board `timeout_900s` dropped **2 real Easy Applies** (ModMed + Salesforce) — `TimeoutExpired` returned before report harvest; Chrome/CF-probe orphans survived | `board_campus_apply`: kill process group on timeout; always `_harvest_portal_report` after timeout/error; accept fresh `startedAt` without `finishedAt` |
| Indeed Easy-Applied Salesforce **Success Architect (service cloud)** — `TITLE_OK` matched architect…cloud; company allowlist kept Salesforce | Expand `TITLE_SKIP` for salesforce/service cloud; skip Salesforce/ServiceNow company without .NET/Azure in title; negative lookbehind so service cloud ≠ cloud stack |
