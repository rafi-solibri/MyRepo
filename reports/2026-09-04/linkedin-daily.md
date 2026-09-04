# LinkedIn daily — 2026-09-04

## Status
**STOPPED** — `account_temporarily_restricted` until **2026-09-10T03:37:00Z**. **0** confirmed applies (none invented).

## Preflight / CDP
- Preflight: OK (`sourceHasAuth` / `destHasAuth` for `li_at`); resume `resumes/Rafi_Resume.docx` ready (20945B, rebuilt from master)
- Restriction flag missing on this VM (`/tmp` + artifacts ephemeral) — restored from 2026-09-03 run memory (`lift_utc=2026-09-10T03:37:00+00:00`)
- `bash scripts/launch-chrome-cdp.sh linkedin` → **exit 7** (refused CDP until lift)
- Did **not** open LinkedIn, login, search, or apply (anti-restriction HARD rule)

## Totals
| Path | Count |
| --- | --- |
| Easy Apply submitted | **0** |
| External / ATS completed | **0** (not started — restriction) |
| Skipped | n/a |
| Blocked | temporary profile-data restriction until 2026-09-10T03:37:00Z |

## Code fix (this run)
None — owner restriction blocker; not code-fixable. People referrals remain off.

## Owner / next cron
1. Do not re-run LinkedIn apply until **2026-09-10 ~03:37 UTC** (plus small buffer)
2. After lift: preflight → CDP → Easy Apply + external pass with pacing (`LINKEDIN_APPLY_PACING_SEC` ≈12s); keep `LINKEDIN_PEOPLE_REFERRALS=0`
3. Careers-only portals may continue without LI (`HITECHCITY_CAREERS_ONLY=1` if needed)

## False-skip suspects
None (no search/apply inventory processed).
