# Hitech City / Knowledge City — issues & fixes

## 2026-08-24 (cloud)

| Issue | Fix |
| --- | --- |
| Gartner Remote-N.A. + AI Strategy title treated as India-remote; Salesforce Hyd <option> click timed out | BAD_LOC_HINT Remote-N.A./North America + CAREERS_TITLE_SKIP/AIML ai strategy; pin_hyderabad_native_select instead of clicking option |
| Owner refreshed master resume Mohammed_Abdul_Rafi_Ahmed_Resume.docx (2026-08-24) | Replaced master + Rafi_Resume.docx alias; JD tailor still on top; upload label stays Rafi_Resume |
| Owner refreshed master resume Mohammed_Abdul_Rafi_Ahmed_Resume.docx (2026-08-23 late) | Replaced master + Rafi_Resume.docx alias (~3.9MB); JD tailor still on top; upload label stays Rafi_Resume |
| Owner refreshed master resume Mohammed_Abdul_Rafi_Ahmed_Resume.docx (2026-08-23 evening) | Replaced resumes/Mohammed_Abdul_Rafi_Ahmed_Resume.docx + Rafi_Resume.docx alias; JD tailor still runs on top; upload filename stays Rafi_Resume |


## 2026-08-23 (cloud)

| Issue | Fix |
| --- | --- |
| Owner supplied new master resume Mohammed_Abdul_Rafi_Ahmed_Resume.docx | Synced into resumes/Rafi_Resume.docx (+ Architect alias); bootstrap prefers owner-named file; JD tailor still runs on top; upload filename/label stays Rafi_Resume |
| resolve_company_f_c hung overnight CDP for 5+ min on Palo Alto /jobs/ (500k innerHTML walk) | link-first f_C scrape + 180k HTML cap + shorter goto_retry; kill/resume path documented in daily report |
| LinkedIn still searched Optum/UHG despite HITECHCITY_SKIP_UHG=1 (careers/boards already skipped) | linkedin_target_apply honors company_skip_reason/skip_uhg before f_C resolve; test covers Optum |


## 2026-08-22 (cloud)

| Issue | Fix |
| --- | --- |
| Oracle careers apply/email soft-incomplete under OWNER_ASLEEP; Salesforce LOC_UI filled Agentforce chat | otp_wall_reason ats_otp_wall fail-fast + Oracle apply-flow checkbox button; location_ui_input_meta_ok skips Agentforce |


## 2026-08-21 (cloud)

| Issue | Fix |
| --- | --- |
| Gartner (Remote- US)/(Remote - U.S.) titles + Workday Remote---Texas paths false-passed location filter; Oracle Performance Test Engineer burned ASK_OWNER | BAD_LOC_HINT: Remote-US/U.S. + full US state names; CAREERS_TITLE_SKIP: performance/load test |


## 2026-08-20 (cloud)

| Issue | Fix |
| --- | --- |
| ATS/AI screening rejects same generic Rafi_Resume.docx on every campus apply | Per-JD truthful tailor (tools/resume_tailor.py): rewrite headline/summary/skill order from owned stack; upload via thread-local path in ATS + LinkedIn Easy Apply; RESUME_TAILOR=1 default |
| Oracle HYDERABAD careers false-skipped via body-line Bengaluru pollution; boards allowlist included Optum/UHG and burned Naukri on Taleo | card_location_ok: Hyd-clean title wins over noisy chrome; drop body-line scrape; exclude Optum/UHG from board allowlist when HITECHCITY_SKIP_UHG=1 |


## 2026-08-17 (cloud)

| Issue | Fix |
| --- | --- |
| PR #206 persist_retry used os.environ in ats_fill.attempt_ats_apply without importing os — parallel workers crashed after ATS submit (NameError) | Add module-level import os in ats_fill.py + unit test that persist_retry env read does not NameError |
| Overnight OWNER_ASLEEP ignored: LinkedIn EXT burned 45+ min on Oracle soft incompletes + double persist_retry with 0 submits | Honor HITECHCITY_OWNER_ASLEEP /tmp flag: 45s ATS cap, 12s ASK_OWNER/captcha park, skip outer persist_retry, soft-incomplete cap 2/company |


## 2026-08-16 (home)

| Issue | Fix |
| --- | --- |
| parallel tabs stole focus so owner missed captcha; one-shot bring_to_front not enough for every daily run | focus_page_for_owner + CDP activate; re-focus every ATS_OWNER_FOCUS_EVERY_SEC=2 during hcaptcha and ASK_OWNER waits; daily_apply/home-headed setdefault |
| parallel multi-tab careers only via one-off launcher; cron/daily risked serial apply | daily_apply setdefault HITECHCITY_PARALLEL_TABS=10 + volume caps; prompt/home-headed/portal-home/rerun document parallel every run |


## 2026-08-16 (home — every-run defaults, owner requirements)

| Issue | Fix |
| --- | --- |
| Owner: do not apply to AI/ML jobs (e.g. AMD Staff/Principal AI/ML Validation) | Hard-skip AI/ML titles in `filters.AIML_TITLE_SKIP` + careers/LI title skips |
| After owner captcha/help, profile left unfinished and runner advanced | Post-captcha `icims=post_captcha_continue`; ASK_OWNER extends while form open; persist_retry on incomplete; never treat invisible hCaptcha/footer as wall |
| Matching jobs left incomplete (Source / required blanks); attempt caps skipped remaining roles | `fill_source_fields` + `fill_validation_gaps`; `ASK_OWNER`/`wait_owner_finish_apply` before incomplete; soft incompletes do not burn attempt caps; headed TIME_CAP≥180 |
| iCIMS Email / I accept / Next not filled (outer login chrome) | Prefer `in_iframe=1`; `icims_fill_gdpr_gate` every iCIMS apply |
| Careers/LinkedIn architect-only; company search no job clicks; location not pinned | Careers expand EM→… + Hyd location pin; LI `geoId=105556991` + `f_C` jobs/search; discovery LI company-search default off |
| Relevant LI/careers hits skipped: Manager of Software Engineering failed TITLE_OK; raw jobPosting ids; careers required Hyd pill | TITLE_OK manager-of/senior-SWE; extract_job_cards; careers apply-bias when no foreign city |
| LI searched architect-first; discovery used Knowledge City/Raheja queries | SEARCH_KEYWORDS EM-first; seeds + employer-name only |
| Owner captcha wait burned full wait after solve | owner_hcaptcha_cleared beyond token; poll 0.4s |


## 2026-08-16 (cloud)

| Issue | Fix |
| --- | --- |
| Gartner Workday Sign In on applyManually + Remote Canada/US burned 390s×N without walling; bare Remote rescued foreign workplaces | Fail-fast workday_stuck_on_sign_in; reject Remote+foreign in card_location_ok/location_allowed; tighten HITECHCITY_MAX_EXT_WALLS=1 MAX_EXT_ATTEMPTS=2 ATS_TIME_CAP=90 |


## 2026-08-15 (home)

| Issue | Fix |
| --- | --- |
| Chrome closed mid-careers after Hyland hCaptcha; remaining tenants all blocked with browser has been closed | Reconnect connect_over_cdp up to HITECHCITY_CAREERS_CDP_RECONNECTS (default 3) instead of burning every company as scan_nav |
| hCaptcha owner-wait poll evaluate hung on cross-origin hcaptcha iframes; CDP connect_over_cdp default 180s starved careers after Chrome flap | Skip hcaptcha/recaptcha frames + 2.5s poll timeout in captcha_solve; connect_over_cdp timeout=20s for discovery/careers/linkedin |


## 2026-08-15 (cloud)

| Issue | Fix |
| --- | --- |
| Accenture/Gartner/DXC/McAfee career URLs extracted 0 jobs (jobdetails + site-search 404) | Match Accenture jobdetails?id= + title=; point Gartner/DXC/McAfee at real job-search URLs |
| Optum/UHG Taleo login tabs poisoned pages[0] and starved other career portals | HITECHCITY_SKIP_UHG (default on) + HITECHCITY_SKIP_COMPANIES; close leftover uhg.taleo tabs so remaining tenants still scan |
| Logged-in Hyland iCIMS jobs stalled on leftover hCaptcha frames at /questions and US EEO forms | Skip captcha wait after Log Out; fill questions + I Don't Wish To Answer / Advance to next form |
| iCIMS 'application was submitted successfully' / 'currently submitted' missed as confirmation | Match those banners + read iCIMS iframe body so already-applied skip works |
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
