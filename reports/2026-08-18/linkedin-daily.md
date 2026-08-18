# LinkedIn daily — 2026-08-18 (post-fix re-run)

## Totals
- Easy Apply submitted: **0**
- External completed: **0**
- Easy Apply skipped: 0 | blocked: 1
- Status: **owner wall — account temporarily restricted until August 18, 2026 9:09 PM PDT**
- Code on this run: `main` @ `46012f5` (`fix(linkedin): primary-location filter, SoC skip, stronger 999 backoff` #209)

## Why no applies
Live CDP opened a LinkedIn **account restriction** page (not a generic CAPTCHA):

> Your account has been temporarily restricted  
> …accessed an unusually high volume of LinkedIn profile data.  
> Your restriction will be lifted on **August 18, 2026 9:09 PM PDT**.

Google session was present. First auto-login still fell through to **password after GSI**, which is the wrong move on a restriction/checkpoint. That is a helper bug (fixed this run). Password/CAPTCHA retries cannot lift an account restriction.

No jobs were submitted. None invented.

## Blocked
- LinkedIn session / Easy Apply | account_restricted until August 18, 2026 9:09 PM PDT | screenshot: `/opt/cursor/artifacts/linkedin-auto-login-captcha.png`

## Code fixes this run
- Detect “temporarily restricted” / lift timestamp; exit as `account_restricted` (do not treat as generic CAPTCHA)
- When Google cookies exist, **do not** fall through to password after GSI
- Easy Apply + CDP live-check fail fast on the same copy

Same-day post-fix re-run cap for this portal is **5**; this job is already inside that cap, so the helper is merged and **no further re-run is launched**.

Artifacts: `/opt/cursor/artifacts/apply-report.json`
