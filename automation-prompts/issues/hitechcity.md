# Hitech City / Knowledge City — issues & fixes

## 2026-08-15 (cloud)

| Issue | Fix |
| --- | --- |
| Owner will not pay CapSolver/2Captcha so unattended iCIMS hCaptcha still blocks Hyland | Headed wait (ATS_CAPTCHA_WAIT_SEC / HOME_LOCAL) + scripts/home-headed-careers-apply.sh so owner clicks captcha for free; paid solver stays optional |
| Hyland iCIMS Apply blocked on hCaptcha so 0 career applies | complete_icims fills email + I accept, clicks checkbox, then CapSolver/2Captcha token inject (same secrets as Indeed); DataDome boards stay owner/residential |
| Hyland iCIMS opened 6 Hyd architect JDs then burned ATS cap — Apply is in iframe and apply lands on GDPR email + hCaptcha | Click iframe mode=apply; fail-fast CAPTCHA/bot wall on iCIMS /login + hCaptcha so the company wall cap trips instead of 6x timeout |
| Hyland/Intel/JPMC jobCount 0 — iCIMS parent chrome (icims in hostname) filled the 40-link cap before the in_iframe listing; Phenom search URLs redirected home | Extract only job-id/path slugs (not vendor hostnames); scan in_iframe first; Hyland URL uses in_iframe=1; rank CAPTCHA hosts later; Phenom search-results URLs |
| Guest ATS boards (Hyland/Intel/JPMC) jobCount 0; Solera already-applied counted as login wall | Wait for Workday/iCIMS/Oracle job cards before extract; already-applied is skip not wall |
| Second careers pass extracted 0 jobs — Frame.evaluate(timeout=) TypeError skipped every frame | Remove invalid evaluate timeout kwarg; hang hosts still skipped so Goldman cannot starve the run |
| Goldman Sachs higher.gs.com hung extract_job_links and starved remaining career portals | Skip hang-scan hosts + 12s evaluate timeout so Workday/iCIMS/Oracle still get applied |
| Careers-only still launched WARP + LinkedIn auto-login (CAPTCHA + ERR_SOCKS on Workday) | HITECHCITY_CAREERS_ONLY skips WARP and LinkedIn auto-login so guest ATS uses direct IP |
| Workday Create Account burned 390s then 0 applies when secret failed tenant complexity / empty /login | Fail-fast inputAlert + standalone /login; Create Account uses deterministic 12+ complexity password so guest Workday can submit |
| Solera Workday Sign In navigated to /login with empty fields; click_advance re-submitted Sign In until 390s timeout | Fail-fast ats_login_wall on standalone myworkdayjobs /login after one credential pass |
| Solera Workday Create Account burned 390s — password-rule error sat below a 1500-char body slice so fail-fast never fired and click_advance kept submitting Create Account | workday_password_alert reads inputAlert + 8k body; do not match static Password Requirements list; wait for Sign In form; skip Create Account submit after reject |
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
