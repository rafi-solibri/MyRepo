# Multi-provider hotel price fetcher

Fetches **4★+** hotel rates for Hyderabad neighbourhoods (Madhapur, Kondapur, Gachibowli, Botanical Garden, Ayyappa Society, 100 Feet Road, Raghavendra Colony) across major OTAs and aggregators.

**Cron / agent runs:** follow [`AUTOMATION.md`](./AUTOMATION.md). Use the nightly entrypoint so every requirement is satisfied — especially the **Qualia Oak / Oak Business Hotel calendars** (current + next month, lowest price across providers), plus all areas, remaining weekends, full inventory, email + CSV.

## Why this exists

Direct scrapes of Booking.com / MakeMyTrip / Yatra from cloud IPs often hit bot walls or HTTP/2 failures. This package:

1. **Kayak India (primary)** — intercepts the live `/i/api/search/dynamic/hotels/poll` JSON, which already includes **per-provider prices** (Booking.com, Agoda, Expedia, brand sites, etc.).
2. **Google Hotels** — second aggregator surface for deals that name MakeMyTrip / Cleartrip / etc.
3. **Direct OTAs** — Booking.com, Agoda, Hotels.com, MakeMyTrip, Goibibo, Cleartrip, EaseMyTrip, Yatra (best-effort; some may return 0 from datacenter IPs).
4. **Merge** — fuzzy hotel-name merge keeps the cheapest rate per provider.

## Setup

```bash
pip install -r tools/hotels/requirements.txt
playwright install chromium   # if browsers are missing
```

## Usage

```bash
# === Preferred for automation (full requirements) ===
PYTHONPATH=. python3 -m tools.hotels.automation -v --out-dir /tmp/hotel-email
# Calendars only (Qualia Oak + Oak Business, current+next month):
PYTHONPATH=. python3 -m tools.hotels.automation --calendars-only -v --out-dir /tmp/hotel-email
# then email (needs RESEND_API_KEY):
PYTHONPATH=. python3 -m tools.hotels.automation --send --out-dir /tmp/hotel-email

# Remaining Sat/Sun this month, all providers
python -m tools.hotels -v --out /tmp/hotels.json --csv /tmp/hotels.csv

# Fast core path (Kayak multi-OTA + Google/Booking/Agoda)
python -m tools.hotels --core -v --out /tmp/hotels.json --csv /tmp/hotels.csv

# One weekend night
python -m tools.hotels \
  --areas Madhapur Kondapur Gachibowli "Botanical Garden" "Ayyappa Society" "100 Feet Road" "Raghavendra Colony" \
  --dates 2026-08-15 \
  --providers kayak google booking agoda \
  --out /tmp/hotels.json --csv /tmp/hotels.csv -v

# Full month weekends
python -m tools.hotels --month 2026-08 --include-past --out /tmp/aug.json
```

Kayak’s poll payload already lists **Booking.com / Agoda / Expedia / brand sites** per hotel, so even `--core` covers multiple OTAs.

## Output

JSON includes `providers_seen`, and each offer has:

- `hotel`, `area`, `date`, `day`, `stars`
- `lowest_price_inr`, `lowest_provider`
- `providers[]` — every OTA price found for that hotel/night

## Notes

- Star class follows what each site reports (Kayak class can include OYO/Townhouse “4★”).
- From many cloud/datacenter IPs, **direct** MakeMyTrip / Goibibo / Yatra / Hotels.com / Booking.com / Agoda pages time out or show bot walls. Kayak still returns those OTAs’ prices inside its poll JSON.
- Chromium is launched with `--disable-http2` to improve odds on Indian OTAs.
- Prefer `python -m tools.hotels --core` for nightly runs; use full provider list when running from a residential IP.
- Prices change quickly — always re-check before booking.

## Tests

```bash
python tools/hotels/tests/test_normalize.py
```
