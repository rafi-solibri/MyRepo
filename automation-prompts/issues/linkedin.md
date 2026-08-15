# LinkedIn — issues & fixes

## 2026-08-15 (cloud)

| Issue | Fix |
| --- | --- |
| Welcome-back login hid Continue with Google; password-first burned CAPTCHA before GSI; google_sso clicked:false | Reveal full form via Sign in using another account; prefer Google SSO when CDP has Google cookies (LINKEDIN_PREFER_GOOGLE_IF_SESSION); click visible GSI frame |


Portal-scoped log. Each daily agent (cloud or home) must append **only** to this file via
`bash scripts/append-issue-fix.sh linkedin "issue" "fix"` — never edit `ISSUES_AND_FIXES.md` for same-day rows.

_No entries yet for this portal on the new per-portal log._
