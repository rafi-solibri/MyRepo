# Hotel Price Tracker — automation runbook

**This is mandatory for every cron / agent run of the Hotel Price Tracker.**  
Do not substitute a smoke test or partial area list unless the user explicitly asks.

## Requirements (all must be satisfied)

| # | Requirement | How |
|---|---|---|
| 1 | **4★+** hotels only | `min_stars=4.0` (default) |
| 2 | **Areas** — Madhapur, Kondapur, Gachibowli, Botanical Garden, Ayyappa Society, 100 Feet Road, Raghavendra Colony | `REQUIRED_AREAS` in `requirements_spec.py` |
| 3 | **Multi-provider prices** (Booking.com, Agoda, Expedia, brand sites, etc.) | Kayak poll JSON (`AUTOMATION_PROVIDERS = kayak`) |
| 4 | **Every remaining Sat/Sun** of the current month | `weekend_dates(...)` |
| 5 | **Full inventory** — every matching hotel-night, not a sample | `python -m tools.hotels.automation` |
| 6 | **Email** tabular HTML, sorted by **date then ascending price** | `report.py` |
| 7 | **CSV attachment** of the full table | attached in Resend payload |
| 8 | **Recipient** `rafi.success@gmail.com` | `EMAIL_TO` |
| 9 | **From** `Hotel Price Watch <onboarding@resend.dev>` until a domain is verified | `EMAIL_FROM` |

## One command (fetch + artifacts)

```bash
cd /workspace   # or repo root
pip install -r tools/hotels/requirements.txt   # if needed
playwright install chromium                    # if needed
PYTHONPATH=. python3 -m tools.hotels.automation -v --out-dir /tmp/hotel-email
```

Produces:

- `/tmp/hotel-email/hotels.json`
- `/tmp/hotel-email/hotels.csv`
- `/tmp/hotel-email/email.html` / `email.txt`
- `/tmp/hotel-email/send-payload.json` (ready for Resend)

## Email delivery (required each run)

1. Create a short-lived Resend API key (`create-api-key`, permission `sending_access`).
2. Send with curl (do **not** use urllib — Cloudflare 1010; do **not** use `FILE:` placeholders in MCP):

```bash
export RESEND_API_KEY='re_...'
PYTHONPATH=. python3 -m tools.hotels.automation --send --out-dir /tmp/hotel-email
# or, if fetch already done:
PYTHONPATH=. python3 -c "from pathlib import Path; from tools.hotels.send_resend import send_payload_file; print(send_payload_file(Path('/tmp/hotel-email/send-payload.json')))"
```

3. Verify with Resend `get-email` — status should be `delivered`.
4. Prefer a **new idempotency key** per calendar day (`…/{run-day}/full` is built in).

## Agent checklist (tick mentally every run)

- [ ] Read `tools/hotels/AUTOMATION.md` and automation memory `hotel-price-watch.md`
- [ ] Ran **full** `python -m tools.hotels.automation` (all 7 areas × remaining weekends)
- [ ] Did **not** stop after a 1-date / 1-area smoke test
- [ ] Emailed **complete** HTML table + CSV to `rafi.success@gmail.com`
- [ ] Confirmed delivery via `get-email`
- [ ] Updated automation memory with the new Resend email id

## Out of scope unless asked

- Changing the recipient or areas
- Merging/deploying unrelated code
- Approving or merging the PR
