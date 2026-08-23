# LinkedIn — issues & fixes

## 2026-08-23 (cloud)

| Issue | Fix |
| --- | --- |
| Search-card / page-wide a[href*=/jobs/view] bait-and-switch: card said .NET Architect (Laureate) but /jobs/view was Azure Data Engineer (Strive4X); Easy Apply hung past time-cap; seed refresh raced before li_at flush | Scope detail_panel_text+parse_card_meta to top-card; re-validate skip_reason/TITLE_OK/location on /jobs/view before Easy Apply; fill_inputs deadline + body.inner_text timeout; seed cookie wait/retry |


## 2026-08-20 (cloud)

| Issue | Fix |
| --- | --- |
| Applications rejected by ATS/AI despite volume — static resume not JD-aligned | Per-job tailor via tools/resume_tailor.py; Easy Apply upload + ATS resume_upload_path active override; python-docx in cloud-agent-install |


## 2026-08-19 (cloud)

| Issue | Fix |
| --- | --- |
| False-allowed Data Engineering / Oracle Cloud SCM / Finance Functional titles | TITLE_BLACKLIST + skip_reason: data engineering/platform, oracle cloud SCM/ERP, finance functional |
| Easy Apply crashed UnboundLocalError: re shadowed by except Exception as re in process_search restore loop | rename except binding to restore_err so module re stays usable |
| auto_login treated temporary account restriction (/checkpoint) as CAPTCHA and aborted cron | detect temporarily restricted + parse lift time; wait within LINKEDIN_RESTRICTION_WAIT_MAX_S then retry; exit 7 if still blocked |


## 2026-08-17 (cloud)

| Issue | Fix |
| --- | --- |
| Primary location Bengaluru/Mumbai false-allowed when workplace scrape contained Hyderabad; SoC hardware titles applied; search nav abandoned after short 999 backoff | location_allowed uses primary location line only (chrome Hyd cannot override); blacklist SoC/ASIC/silicon; search goto 5 tries with longer HTTP_RESPONSE_CODE backoff |


## 2026-08-15 (cloud)

| Issue | Fix |
| --- | --- |
| 9× did not leave LinkedIn — Apply stayed on job view; only 20 generic hrefs scanned | window.open hook + data-tracking-control-name apply + companyApplyUrl JSON + hop dest; shared extract_offsite_from_text |
| Company-site completer burned budget on Workday maintenance and Indeed OneClick | Shared complete.py fail-fast unavailable + prefer guest apply |
| Non-EA company-site search skipped after 20 Easy Applies / daily limit so external inventory stayed empty | Always run non-EA pass; MAX_EXTERNAL 40; Workday country/education + Greenhouse combos |
| External ATS completed 0 most days — thin fill + 3.5m cap + stayed on LinkedIn | Shared tools/ats/complete.py (Workday create-account + Greenhouse/generic); 6.5m cap; follow offsite href |
| Welcome-back login hid Continue with Google; password-first burned CAPTCHA before GSI; google_sso clicked:false | Reveal full form via Sign in using another account; prefer Google SSO when CDP has Google cookies (LINKEDIN_PREFER_GOOGLE_IF_SESSION); click visible GSI frame |


Portal-scoped log. Each daily agent (cloud or home) must append **only** to this file via
`bash scripts/append-issue-fix.sh linkedin "issue" "fix"` — never edit `ISSUES_AND_FIXES.md` for same-day rows.

_No entries yet for this portal on the new per-portal log._
