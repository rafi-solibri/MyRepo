#!/usr/bin/env python3
"""End-to-end Hotel Price Tracker automation run.

Satisfies every product requirement in ``requirements_spec``:
  - **MOST IMPORTANT:** Qualia Oak + Oak Business Hotel calendars
    (current + next month, lowest price across providers per night)
  - all required Hyderabad areas, 4★+, remaining Sat/Sun
  - multi-OTA prices via Kayak poll
  - full inventory email (calendars first) + CSVs to rafi.success@gmail.com

Usage:
  PYTHONPATH=. python3 -m tools.hotels.automation
  PYTHONPATH=. python3 -m tools.hotels.automation --calendars-only
  PYTHONPATH=. python3 -m tools.hotels.automation --send   # needs RESEND_API_KEY
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import date, datetime
from pathlib import Path

from .calendar_prices import fetch_tracked_calendars
from .fetch import fetch_prices, weekend_dates
from .report import write_report_artifacts
from .requirements_spec import (
    ADULTS,
    AUTOMATION_PROVIDERS,
    CALENDAR_HOTELS,
    EMAIL_TO,
    MIN_STARS,
    REQUIRED_AREAS,
)
from .send_resend import send_payload_file

log = logging.getLogger(__name__)


def run_nightly(
    *,
    out_dir: Path,
    send: bool = False,
    include_past: bool = False,
    month: str | None = None,
    headed: bool = False,
    calendars_only: bool = False,
    skip_calendars: bool = False,
) -> dict:
    today = date.today()
    if month:
        year, mon = map(int, month.split("-"))
    else:
        year, mon = today.year, today.month

    dates = weekend_dates(year, mon, include_past=include_past, today=today)
    month_label = f"{year:04d}-{mon:02d}"
    run_day = today.isoformat()

    calendars_payload: list[dict] = []
    if not skip_calendars:
        log.info(
            "PRIORITY: fetching calendars for %s (current + next month)",
            ", ".join(h["name"] for h in CALENDAR_HOTELS),
        )
        calendars = fetch_tracked_calendars(
            today=today,
            adults=ADULTS,
            headless=not headed,
            hotels=CALENDAR_HOTELS,
        )
        calendars_payload = [c.to_dict() for c in calendars]
        for c in calendars:
            priced = [d for d in c.days if d.lowest_price_inr is not None]
            cheapest = min((d.lowest_price_inr for d in priced), default=None)
            log.info(
                "Calendar %s: %d/%d nights priced, cheapest=%s",
                c.hotel,
                len(priced),
                len(c.days),
                cheapest,
            )
    else:
        log.warning("skip_calendars=True — violating most-important requirement")

    offers = []
    if not calendars_only:
        log.info(
            "Weekend inventory areas=%s dates=%s providers=%s min_stars=%s",
            list(REQUIRED_AREAS),
            [d.isoformat() for d in dates],
            list(AUTOMATION_PROVIDERS),
            MIN_STARS,
        )
        if not dates:
            log.warning("No remaining weekend dates in %s", month_label)
        else:
            offers = fetch_prices(
                areas=REQUIRED_AREAS,
                dates=dates,
                providers=AUTOMATION_PROVIDERS,
                min_stars=MIN_STARS,
                adults=ADULTS,
                merge=True,
                headless=not headed,
            )

    from .normalize import summarize_by_provider

    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "areas": list(REQUIRED_AREAS),
        "providers_requested": list(AUTOMATION_PROVIDERS),
        "providers_seen": summarize_by_provider(offers),
        "min_stars": MIN_STARS,
        "count": len(offers),
        "offers": [o.to_dict() for o in offers],
        "calendars": calendars_payload,
        "requirements": {
            "email_to": EMAIL_TO,
            "priority_calendars": [h["name"] for h in CALENDAR_HOTELS],
            "calendar_months": "current_and_next",
            "full_inventory": not calendars_only,
            "sort": "date_asc_then_price_asc",
            "weekend_scope": month_label,
            "dates": [d.isoformat() for d in dates],
        },
    }

    if not calendars_payload and not skip_calendars:
        raise RuntimeError("Calendar fetch returned empty — aborting (priority requirement)")

    idem = f"hotel-weekend-prices/{month_label}/{EMAIL_TO}/{run_day}/full-with-calendars"
    paths = write_report_artifacts(
        payload,
        out_dir,
        idempotency_key=idem,
        month_label=month_label,
    )
    log.info(
        "Wrote calendars=%d offers=%d | html=%s payload=%s",
        len(calendars_payload),
        len(offers),
        paths["html"],
        paths["send_payload"],
    )

    result = {
        "count": len(offers),
        "calendars": len(calendars_payload),
        "dates": [d.isoformat() for d in dates],
        "areas": list(REQUIRED_AREAS),
        "paths": {k: str(v) for k, v in paths.items()},
        "email_id": None,
    }

    if send:
        resp = send_payload_file(paths["send_payload"])
        result["email_id"] = resp.get("id")
        (out_dir / "send-response.json").write_text(json.dumps(resp, indent=2))
        log.info("Emailed %s id=%s", EMAIL_TO, result["email_id"])
    else:
        log.info(
            "Email payload ready for %s. Set RESEND_API_KEY and pass --send, "
            "or curl %s to https://api.resend.com/emails",
            EMAIL_TO,
            paths["send_payload"],
        )

    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("/tmp/hotel-email"),
        help="Directory for JSON/CSV/HTML/send-payload artifacts",
    )
    parser.add_argument("--month", help="YYYY-MM for weekend scan (default: current month)")
    parser.add_argument(
        "--include-past",
        action="store_true",
        help="Include past Sat/Sun in the weekend month scan",
    )
    parser.add_argument(
        "--calendars-only",
        action="store_true",
        help="Only build Qualia Oak / Oak Business calendars (skip area weekend scan)",
    )
    parser.add_argument(
        "--skip-calendars",
        action="store_true",
        help="Do not fetch priority calendars (not allowed for scheduled runs)",
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send email via Resend (requires RESEND_API_KEY)",
    )
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    result = run_nightly(
        out_dir=args.out_dir,
        send=args.send,
        include_past=args.include_past,
        month=args.month,
        headed=args.headed,
        calendars_only=args.calendars_only,
        skip_calendars=args.skip_calendars,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
