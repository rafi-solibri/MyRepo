# Hotel Price Tracker — issues & fixes

## 2026-08-14 (cloud)

| Issue | Fix |
| --- | --- |
| Google calendar enrich used $12 GREAT PRICE chips (₹1044 at FX 87) as nightly mins and overwrote real Kayak OTA rates on Qualia Oak / Oak Business | Raise Google MIN_USD to 18 / MIN_INR to 1500; skip UI-chip names; unlabeled Google/Google Hotels page-min cannot undercut Kayak; sanitize before email. Sent 2026-08-14 Resend 42edf00a-1f5d-496b-b8ad-59965112bb74 (delivered) |


Portal-scoped log. Each daily agent (cloud or home) must append **only** to this file via
`bash scripts/append-issue-fix.sh hotels "issue" "fix"` — never edit `ISSUES_AND_FIXES.md` for same-day rows.

_No entries yet for this portal on the new per-portal log._
