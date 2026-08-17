# LinkedIn — issues & fixes

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
