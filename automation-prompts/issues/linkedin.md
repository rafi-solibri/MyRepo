# LinkedIn — issues & fixes

## 2026-08-25 (cloud)

| Issue | Fix |
| --- | --- |
| preflight sync-chrome-sessions unbound DESTS after hirist portal added (arrays length mismatch) | Same-day fix already on main via #257 (hirist dest+token; REQUIRED optional for hirist/linkedin_alt); this run recorded report + confirmed preflight after pull |


## 2026-08-24 (cloud)

| Issue | Fix |
| --- | --- |
| Cron: stale Google cookies + LINKEDIN_PASSWORD rejected; password retries tripped Security Verification CAPTCHA (exit 6) | Land prior unmerged auto_login: wrong-password detect (incl Wrong email or password), GSI identifier/password fill, secret alias candidates, per-method timeout; owner must refresh LINKEDIN_PASSWORD/GOOGLE_PASSWORD then headed-login if CAPTCHA persists |
| Portal banner Wrong email or password was not matched so rejected secrets timed out as generic login_required | Match that phrase in wrong-password detector; owner must refresh password secrets or headed-login + session seed |
| Stale li_at + GSI identifier form + wrong-password timed out as generic login fail; fix never reached main (gh pr create denied) | Detect wrong password; complete Google identifier/password; try secret aliases; per-method timeout |
| Owner refreshed master resume Mohammed_Abdul_Rafi_Ahmed_Resume.docx (2026-08-24) | Replaced master + Rafi_Resume.docx alias; JD tailor still on top; upload label stays Rafi_Resume |
| Owner refreshed master resume Mohammed_Abdul_Rafi_Ahmed_Resume.docx (2026-08-23 late) | Replaced master + Rafi_Resume.docx alias (~3.9MB); JD tailor still on top; upload label stays Rafi_Resume |
| Owner refreshed master resume Mohammed_Abdul_Rafi_Ahmed_Resume.docx (2026-08-23 evening) | Replaced resumes/Mohammed_Abdul_Rafi_Ahmed_Resume.docx + Rafi_Resume.docx alias; JD tailor still runs on top; upload filename stays Rafi_Resume |


## 2026-08-23 (cloud)

| Issue | Fix |
| --- | --- |
| Owner supplied new master resume Mohammed_Abdul_Rafi_Ahmed_Resume.docx | Synced into resumes/Rafi_Resume.docx (+ Architect alias); bootstrap prefers owner-named file; JD tailor still runs on top; upload filename/label stays Rafi_Resume |
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
