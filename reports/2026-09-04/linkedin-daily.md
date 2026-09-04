# LinkedIn daily — 2026-09-04

## Status
**STOPPED** — `account_temporarily_restricted` until **2026-09-10T03:37:00Z**. **0** confirmed applies (none invented).

This is the same-day **POST_FIX_RERUN=1** on merged `#320` (`34c296f`). The earlier morning run did not apply with the fix; this session executed the daily job **with the merged code**. Applies still cannot happen until lift (anti-restriction HARD rule).

## Preflight / CDP
- `git fetch/checkout/pull origin main` → `34c296f` fix(linkedin): persist restriction lift in `.portal-sessions` seed (#320)
- Preflight: OK (`sourceHasAuth` / `destHasAuth` for `li_at`); resume `resumes/Rafi_Resume.docx` ready (20945B, rebuilt from master)
- Restriction seed present on this VM (`.portal-sessions/linkedin-restriction-until.json`, `lift_utc=2026-09-10T03:37:00+00:00`)
- `bash scripts/launch-chrome-cdp.sh linkedin` → **exit 7** (refused CDP until lift) — merged #320 behavior confirmed
- `python3 tools/linkedin/linkedin_easy_apply.py` → **exit 7** (restriction skip; no search/apply)
- `python3 tools/linkedin/linkedin_external_apply.py` → first pass tried CDP (`ECONNREFUSED`); after helper fix, **exit 7** without opening Chrome
- Did **not** open LinkedIn, login, search, or apply (anti-restriction HARD rule)

## Totals
| Path | Count |
| --- | --- |
| Easy Apply submitted | **0** |
| External / ATS completed | **0** (not started — restriction) |
| Skipped | n/a (no inventory processed) |
| Blocked | temporary profile-data restriction until 2026-09-10T03:37:00Z |

## Code fix (this re-run)
External ATS helper connected to CDP even when restriction memory said skip. Honor `should_skip_linkedin_for_restriction()` and exit 7 before Playwright, matching Easy Apply + `launch-chrome-cdp.sh`.

## Owner / next cron
1. Do not re-run LinkedIn apply until **2026-09-10 ~03:37 UTC** (plus small buffer)
2. After lift: preflight → CDP → Easy Apply + external pass with pacing (`LINKEDIN_APPLY_PACING_SEC` ≈12s); keep `LINKEDIN_PEOPLE_REFERRALS=0`
3. Careers-only portals may continue without LI (`HITECHCITY_CAREERS_ONLY=1` if needed)

## False-skip suspects
None (no search/apply inventory processed).
