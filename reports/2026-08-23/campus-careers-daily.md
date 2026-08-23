# Knowledge City / campus careers daily — 2026-08-23 (post-fix re-run 2 of 5)

## Totals (confirmation only)
- **Submitted: 0** | Referrals: 0 | Blocked: 30 | Skipped: 30 | Chat rows: 60
- Success rule: confirmation text only. **No invented applies.**
- Already-applied today from the earlier re-run (`bc-df32c2a1`): none
- Report: `/opt/cursor/artifacts/` campus-careers daily JSON (confirmation-only)

## What this re-run executed
1. Checked out latest `main` (`df7b068`, merged [#244](https://github.com/rafi-solibri/MyRepo/pull/244) resume master)
2. Preflight + headed Chrome CDP (careers-only=1, no LinkedIn WARP/CAPTCHA wait)
3. `python3 tools/.../daily_apply.py` with parallel tabs=10 (careers-only)
4. Discovery: **92** campus tenants (0 added)

LinkedIn and boards were skipped (careers-only) so company career portals ran first.

## Code fixes landed on this branch
Cherry-picked from today's first re-run (never merged) plus new hang guards:

| Fix | Why |
| --- | --- |
| Hyd listing apply-bias + iCIMS iframe rank | Title-only Hyd-pinned cards extracted 0 jobs |
| Honor `listingLoc` in `apply_job` | Hyland .NET / Blue Yonder false-skipped after extract |
| ASK_OWNER fail-fast on `ats_otp_wall` | Oracle OTP fingerprint churn extended forever |
| Prefer `.NET` titles before captcha wall cap | Hyland burned walls on Performance/AE first |
| SIGALRM hang-guard + skip ad frames | Playwright `inner_text` ignored timeouts after JS-dialog errors |
| Cap listing `wait_for_selector` with SIGALRM | Workers froze in extract wait at 73% CPU |

PR create in this environment requires owner approval (agent feature branch).

## Owner-only walls (not code-fixable)
- Hyland / AMD iCIMS **hCaptcha** (`owner_captcha_unsolved`) — Senior Software Architect - .NET opened
- JPMorgan Chase **CAPTCHA/bot wall** (Hyd Director / Lead Software Engineer)
- Oracle **email OTP** (`ats_otp_wall`) — Principal Core Infrastructure Engineer HYDERABAD
- ModMed / Gartner **Workday Sign In**
- Cognizant talent portal **no guest ATS form** / 403
- Deloitte careers **406**
- Blue Yonder cards still `location_non_hyd_city` except listing-bias opens that did not confirm

Headed Chrome stayed up for owner clicks; captcha waits were capped so parallel workers could continue.

## Passes
| Pass | Result |
| --- | --- |
| 1 | Listing bias worked (Hyland .NET opened); Playwright inner_text hung past 180s |
| 2 | Thread hang-timeout broke Playwright greenlets (68k log lines) — reverted |
| 3 | SIGALRM + 30s ASK_OWNER; Oracle OTP fail-fast; 0 confirmation |
| 4 | Skipped proven Oracle/Gartner walls; IBM/Cognizant attempted; CDP wedged again; **0 confirmation** |

## Owner actions
1. Click Hyland/AMD iCIMS hCaptcha and JPMC bot wall in headed Chrome
2. Complete Oracle email OTP
3. Approve/merge the apply-path + hang-guard PR so tomorrow's cron has the fixes
