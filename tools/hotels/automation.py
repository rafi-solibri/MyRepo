#!/usr/bin/env python3
"""End-to-end Hotel Price Tracker automation run.

Satisfies every product requirement in ``requirements_spec``:
  - all required Hyderabad areas
  - 4★+ only
  - multi-OTA prices via Kayak poll
  - remaining Sat/Sun of the current month
  - full inventory (not a sample)
  - email tabular HTML + CSV to the configured recipient

Usage:
  PYTHONPATH=. python3 -m tools.hotels.automation
  PYTHONPATH=. python3 -m tools.hotels.automation --send   # needs RESEND_API_KEY
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date, datetime
from pathlib import Path

from .fetch import fetch_prices, weekend_dates
from .report import write_report_artifacts
from .requirements_spec import (
    ADULTS,
    AUTOMATION_PROVIDERS,
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
) -> dict:
    today = date.today()
    if month:
        year, mon = map(int, month.split("-"))
    else:
        year, mon = today.year, today.month

    dates = weekend_dates(year, mon, include_past=include_past, today=today)
    month_label = f"{year:04d}-{mon:02d}"
    run_day = today.isoformat()

    log.info(
        "Nightly run areas=%s dates=%s providers=%s min_stars=%s",
        list(REQUIRED_AREAS),
        [d.isoformat() for d in dates],
        list(AUTOMATION_PROVIDERS),
        MIN_STARS,
    )
    if not dates:
        raise RuntimeError(f"No remaining weekend dates in {month_label}")

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
        "requirements": {
            "email_to": EMAIL_TO,
            "full_inventory": True,
            "sort": "date_asc_then_price_asc",
            "weekend_scope": month_label,
            "dates": [d.isoformat() for d in dates],
        },
    }

    idem = f"hotel-weekend-prices/{month_label}/{EMAIL_TO}/{run_day}/full"
    paths = write_report_artifacts(
        payload,
        out_dir,
        idempotency_key=idem,
        month_label=month_label,
    )
    log.info(
        "Wrote %d offers | json=%s csv=%s payload=%s",
        len(offers),
        paths["json"],
        paths["csv"],
        paths["send_payload"],
    )

    result = {
        "count": len(offers),
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
    parser.add_argument(
        "--month",
        help="YYYY-MM (default: current month)",
    )
    parser.add_argument(
        "--include-past",
        action="store_true",
        help="Include past Sat/Sun in the month",
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
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
