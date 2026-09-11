# Hotel Price Watch — automation memory

Last successful full run (on-demand 2026-09-11 IST):

| Field | Value |
|---|---|
| Run day | 2026-09-11 |
| Resend email id | `41744270-254a-4587-a9bd-bb6f0a1d3ad7` |
| Delivery status | **delivered** |
| To | [REDACTED] |
| From | Hotel Price Watch \<onboarding@resend.dev\> |
| Calendars | Qualia Oak **51/51** (cheapest ₹1,552 Agoda), Oak Business **50/51** (cheapest ₹1,670 Agoda; 2026-09-11 empty after dropping Google $12 crumb with no Kayak rate) |
| Weekend inventory | **493** offers (4★+, 7 areas, remaining Sat/Sun 12/13/19/20/26/27) after sanitize from 545 raw-merged |
| Dates | 2026-09-12, 13, 19, 20, 26, 27 |
| Artifacts | `/tmp/hotel-email/` and `/opt/cursor/artifacts/hotel-email/` |

Notes:
- First calendar merge logged cheapest=₹1044 (`$12` GREAT PRICE chip). Re-applied unmerged 2026-08-14 guard (`MIN_USD=18` / `MIN_INR=1500`, bare Google page-min cannot undercut Kayak) and sanitized artifacts before send.
- 100 Feet Road 2026-09-12 Google Hotels goto timed out; Kayak still returned offers for that cell.
- Idempotency key: `hotel-weekend-prices/2026-09/[REDACTED]/2026-09-11/full-with-calendars-070606`.
