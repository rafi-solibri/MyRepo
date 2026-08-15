# Hitech City / Knowledge City — issues & fixes

## 2026-08-15 (cloud)

| Issue | Fix |
| --- | --- |
| Career portals applied 0 — JD Sign-in chrome and Workday Create Account treated as login wall | Do not wall JD chrome or Workday auth; Sign In first; adopt ATS tabs; skip Amazon/Microsoft/Qualcomm SSO-only hosts; run careers before LinkedIn |
| 403 / Microsoft Eightfold SSO chooser + silicon/product-design + Ionic/Zscaler JDs | fail-fast 403+SSO chooser; fingerprint stuck Apply; poll Apply tabs 6s; skip silicon engineer/product design manager |
| Solera Workday Create Account burned 390s on password-rule reject | workday_auth fail-fasts password-must-include; try Sign In once then ats_login_wall |
| Qualcomm Eightfold email-only Sign-in burned 390s ATS cap (timeout not a wall) | auth_wall_reason fail-fast email-only SSO; talent.cognizant.com/login2; skip silicon design titles |
| Cognizant/Eightfold SSO burned ATS cap; brochure careers pages timed out | auth_wall_url fail-fast login.cognizant + eightfold.ai/login; shared no_ats_form + skip View applied CTAs |
| Workday maintenance and SmartRecruiters OneClick burned ATS budget then tripped walls | Shared completer fail-fasts maintenance; skips OneClick/Indeed OAuth; timeouts/unavailable are not company walls |
| First ATS timeout counted as company wall (cap 1) so remaining externals were skipped | is_hard_ats_wall ignores timeout/incomplete; caps 4 walls / 10 attempts |
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
