#!/usr/bin/env python3
"""CLI for multi-provider Hyderabad weekend hotel price fetches."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from datetime import date, datetime
from pathlib import Path

from .fetch import DEFAULT_AREAS, fetch_prices, weekend_dates
from .normalize import summarize_by_provider
from .providers import CORE_PROVIDERS, DEFAULT_PROVIDERS


def _parse_dates(values: list[str] | None) -> list[date] | None:
    if not values:
        return None
    out: list[date] = []
    for v in values:
        out.append(datetime.strptime(v, "%Y-%m-%d").date())
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--areas",
        nargs="+",
        default=list(DEFAULT_AREAS),
        help=(
            "Neighbourhoods to search (default: Madhapur Kondapur Gachibowli "
            "Botanical Garden Ayyappa Society 100 Feet Road Raghavendra Colony)"
        ),
    )
    parser.add_argument(
        "--dates",
        nargs="+",
        help="Check-in dates YYYY-MM-DD (default: remaining Sat/Sun this month)",
    )
    parser.add_argument(
        "--month",
        help="Use all weekends in YYYY-MM (overrides --dates if set with --all-month)",
    )
    parser.add_argument(
        "--include-past",
        action="store_true",
        help="Include past weekend dates in the month",
    )
    parser.add_argument(
        "--providers",
        nargs="+",
        default=None,
        choices=DEFAULT_PROVIDERS,
        help="Providers to query (default: all)",
    )
    parser.add_argument(
        "--core",
        action="store_true",
        help="Only Kayak/Google/Booking/Agoda (faster; Kayak still covers many OTAs)",
    )
    parser.add_argument("--min-stars", type=float, default=4.0)
    parser.add_argument("--adults", type=int, default=2)
    parser.add_argument("--out", type=Path, default=Path("hotel_prices.json"))
    parser.add_argument("--csv", type=Path, help="Optional CSV export path")
    parser.add_argument("--no-merge", action="store_true")
    parser.add_argument("--headed", action="store_true", help="Show browser windows")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    dates = _parse_dates(args.dates)
    if args.month:
        year, month = map(int, args.month.split("-"))
        dates = weekend_dates(year, month, include_past=args.include_past)

    providers = args.providers
    if providers is None:
        providers = CORE_PROVIDERS if args.core else DEFAULT_PROVIDERS

    offers = fetch_prices(
        areas=args.areas,
        dates=dates,
        providers=providers,
        min_stars=args.min_stars,
        adults=args.adults,
        merge=not args.no_merge,
        headless=not args.headed,
    )

    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "areas": args.areas,
        "providers_requested": providers,
        "providers_seen": summarize_by_provider(offers),
        "min_stars": args.min_stars,
        "count": len(offers),
        "offers": [o.to_dict() for o in offers],
    }
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"Wrote {len(offers)} offers -> {args.out}")
    print("Providers seen:", payload["providers_seen"])

    if args.csv:
        with args.csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(
                [
                    "Date",
                    "Day",
                    "Hotel",
                    "Area",
                    "Stars",
                    "Lowest Price (INR)",
                    "Lowest Provider",
                    "All Providers",
                    "Source",
                ]
            )
            for o in offers:
                all_p = "; ".join(f"{p.provider}=₹{p.price_inr}" for p in o.providers)
                w.writerow(
                    [
                        o.check_in.isoformat(),
                        o.day,
                        o.hotel,
                        o.area,
                        o.stars,
                        o.lowest_price_inr,
                        o.lowest_provider,
                        all_p,
                        o.source,
                    ]
                )
        print(f"Wrote CSV -> {args.csv}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
