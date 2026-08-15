# Hitech City / Knowledge City — issues & fixes

## 2026-08-15 (cloud)

| Issue | Fix |
| --- | --- |
| External ATS time cap 45s/90s burned Workday/Greenhouse before submit | Default EXT/careers ATS cap 390s; attempt_ats_apply uses shared complete_ats |
| Foundit/Naukri skipped Solution Architecture titles (no Architect word); LinkedIn discovery merged junk tenants (software companies erbil, Hyderabad Tech Community) | Match architect(?:ure)? in arch/lead filters; reject+prune junk LinkedIn discovery names |


## 2026-08-14 (home)

| Issue | Fix |
| --- | --- |
| Experian SmartRecruiters OneClick opened Indeed OAuth tabs; careers hung burning ATS time cap; Principal Physical Design matched TITLE_HINT | auth_wall_url + timed inner_text; close Indeed SSO popups; careers wall/attempt caps; CAREERS_TITLE_SKIP physical design/chiplet/ASIC |
Portal-scoped log. Each daily agent (cloud or home) must append **only** to this file via
`bash scripts/append-issue-fix.sh hitechcity "issue" "fix"` — never edit `ISSUES_AND_FIXES.md` for same-day rows.

## 2026-08-14 (cloud)

| Issue | Fix |
| --- | --- |
| parallel portal PRs collided on shared issues log | portal-scoped issues/hitechcity.md only |
| Indeed board `timeout_900s` dropped **2 real Easy Applies** (ModMed + Salesforce) — `TimeoutExpired` returned before report harvest; Chrome/CF-probe orphans survived | `board_campus_apply`: kill process group on timeout; always `_harvest_portal_report` after timeout/error; accept fresh `startedAt` without `finishedAt` |
| Indeed Easy-Applied Salesforce **Success Architect (service cloud)** — `TITLE_OK` matched architect…cloud; company allowlist kept Salesforce | Expand `TITLE_SKIP` for salesforce/service cloud; skip Salesforce/ServiceNow company without .NET/Azure in title; negative lookbehind so service cloud ≠ cloud stack |
