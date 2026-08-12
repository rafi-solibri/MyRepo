# Cutshort home daily 2026-08-12

## Counts
- Scanned: **1929**
- Qualifying: **0**
- Applied: **0**
- Already: 0
- Failed/blocked (apply): 0
- External: 0
- Q answered: **0** | already-submitted: 30 | locked-empty: **322** | verify-empty: 0
- Awaiting listed: 356
- Failures (apply + locked-empty + verify-empty): **322**

## Applied
_None_

## Failed applies
_None_

## Notes
- Live CDP session OK (`cutshort_authentication` + candidate dashboard).
- Preflight SQLite false-failed while Chrome Default was open (`chrome_cookies_locked`) — continued after `wait_for_cdp_login.js`.
- Inventory audit: Hyd/remote Architect/Tech Lead/.NET roles with listed CTC ≥35L were absent; remaining “interesting” Hyd hits were Data Architect (hard-skip) or CTC &lt;35L.
- Cloud morning run already applied Firmware Lead @ Gradera (`69d632ec8d4a3a2dd0b209b3`).
- JSON: `artifacts/cutshort-daily-run.json` → publish to `automation-results`

## Code fix (this run)
- `tools/chrome_session.js`: extend live CDP preflight fallback to cutshort/foundit/instahyre
