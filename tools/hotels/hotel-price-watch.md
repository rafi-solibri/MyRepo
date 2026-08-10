# Hotel Price Watch — automation memory

Last successful full run (manual re-run for Mohammed Abdul Rafi Ahmed):

| Field | Value |
|---|---|
| Run day | 2026-08-10 |
| Resend email id | `6f32e5c5-6743-434a-9d78-e22287358f24` |
| Delivery status | **delivered** |
| To | rafi.success@gmail.com |
| From | Hotel Price Watch \<onboarding@resend.dev\> |
| Calendars | Qualia Oak **52/52**, Oak Business **52/52** (Aug+Sep 2026) |
| Weekend inventory | **258** offers (4★+, 7 areas, remaining Sat/Sun) |
| Dates | 2026-08-15, 16, 22, 23, 29, 30 |
| Artifacts | `/tmp/hotel-email/` and `/opt/cursor/artifacts/hotel-email/` |

Notes:
- Idempotency key reused same-day body → appended `-rerun-085555` for this send.
- Raghavendra Colony 2026-08-29 and 2026-08-30 returned 0 Kayak offers; other dates for that area OK.
