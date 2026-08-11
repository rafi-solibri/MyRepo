# Instahyre home daily 2026-08-11

**STOP: Instahyre CDP login missing (Windows App-Bound Encryption).**

- Preflight: `destHasAuth: false` for `~/.cursor/chrome-cdp-profiles/instahyre` (`sessionid` needed)
- Desktop Default → CDP cookie copy skipped (Chrome v20 ABE)
- Applied: **0** | Seen: **0** | Blocked: **1**
- JSON: `artifacts/instahyre-daily-run.json` → `automation-results/instahyre/2026-08-11.json`

## Owner action (required)
1. Close other Chrome windows using the same CDP port if needed.
2. Run: `bash scripts/home-headed-login.sh instahyre`
3. Sign in at https://www.instahyre.com/login/ (rafi.success@gmail.com) in the headed window.
4. Confirm https://www.instahyre.com/candidate/opportunities/ loads, press Enter to verify.
5. Re-run: `bash scripts/portal-home-daily.sh instahyre` or `node tools/instahyre/daily_apply.js`

## Code shipped this run
- `tools/instahyre/wait_for_cdp_login.js` + `home-headed-login.sh` wiring (live probe parity with Cutshort/LinkedIn)
