# Instahyre home daily 2026-08-15

Mohammed Abdul Rafi Ahmed | Expected **65 LPA** / Current **52 LPA** | Hyd + Remote | resume `Rafi_Resume.docx`

## Totals

| Metric | Count |
| --- | ---: |
| Applied (Instahyre in-app) | 0 |
| External ATS completed | 0 |
| Skipped | 677 |
| Blocked | 0 |
| Seen | 677 |

## Submitted

_None — inventory already swept (interested stayed 449)._

## Top skip reasons

- location_not_hyd_remote: 551
- already_interested: 89
- generic_engineering_without_dotnet_cloud: 24
- pure_ai_data_without_dotnet: 6
- java_primary: 4

## Notes

- Live CDP session OK (`sessionid` + opportunities dashboard) after `newPage` fix.
- Preflight SQLite showed cookies locked / `destHasAuth: false` — continued with live CDP.
- Opportunities undecided: 3 — all correctly skipped for location (Sigmoid Bangalore, Bupa Gurgaon, DTDL Gurgaon).
- Prior Chrome session restore left 100+ Foundit/Cognizant tabs → Playwright `connectOverCDP` hung; fixed launch clean-exit + crash-restore flags.
- JSON: `artifacts/instahyre-daily-run.json` → `automation-results/instahyre/2026-08-15.json`

## Code fix

- `tools/instahyre/daily_apply.js` + `wait_for_cdp_login.js`: always `context.newPage()` (foreign `pages()[0]` caused `ERR_ABORT` / false login wall).
- `scripts/launch-chrome-cdp.sh`: mark Preferences clean exit + disable session-restore bubbles after `taskkill`.
