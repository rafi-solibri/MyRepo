"""Enrich tracked-hotel calendars with Google Hotels deal ladder prices.

For each night, open the Google Hotels hotel page (or search), scrape the
provider ladder, and take the minimum. Cut body text before "Similar hotels"
so nearby-property prices are not mixed in.
"""

from __future__ import annotations

import logging
import re
import time
from datetime import date, timedelta
from typing import Any
from urllib.parse import quote

from playwright.sync_api import BrowserContext, Page

from .browser import browser_session, dismiss_overlays
from .calendar_prices import DayPrice, HotelCalendar
from .providers.google_hotels import (
    DEFAULT_USD_INR,
    INR_PRICE_RE,
    MIN_INR,
    MIN_USD,
    USD_PRICE_RE,
)

log = logging.getLogger(__name__)

PROVIDER_NAMES = (
    "MakeMyTrip",
    "Booking.com",
    "Agoda",
    "Cleartrip",
    "EaseMyTrip",
    "Yatra",
    "Goibibo",
    "Hotels.com",
    "Expedia",
    "Google Hotels",
)


def _hotel_url(hotel: dict[str, str], cin: date, adults: int = 2) -> str:
    cout = cin + timedelta(days=1)
    q = hotel.get("google_query") or f"{hotel['name']} Hyderabad"
    return (
        "https://www.google.com/travel/hotels?"
        f"q={quote(q)}"
        f"&dates={cin.isoformat().replace('-', '')},{cout.isoformat().replace('-', '')}"
        f"&adults={adults}&hl=en-IN&gl=in&curr=INR"
    )


def _cut_similar(text: str) -> str:
    for marker in ("Similar hotels", "People also searched", "More hotels"):
        idx = text.find(marker)
        if idx >= 0:
            return text[:idx]
    return text


def _line_prices(line: str) -> list[int]:
    inr_vals = [int(x.replace(",", "")) for x in INR_PRICE_RE.findall(line)]
    prices = [p for p in inr_vals if MIN_INR <= p <= 200_000]
    if prices:
        return prices
    usd_vals: list[int] = []
    for raw in USD_PRICE_RE.findall(line):
        try:
            usd = float(raw.replace(",", ""))
        except ValueError:
            continue
        if usd < MIN_USD:
            continue
        usd_vals.append(int(round(usd * DEFAULT_USD_INR)))
    return [p for p in usd_vals if MIN_INR <= p <= 200_000]


def _match_provider(line: str) -> str | None:
    for name in PROVIDER_NAMES:
        if name.lower() in line.lower():
            return name
    return None


def _parse_ladder(text: str) -> dict[str, int]:
    """Best-effort provider → INR from Google Hotels ladder text."""
    text = _cut_similar(text)
    providers: dict[str, int] = {}
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    pending_provider: str | None = None
    for i, line in enumerate(lines):
        matched = _match_provider(line)
        prices = _line_prices(line)
        if matched and prices:
            if matched not in providers or min(prices) < providers[matched]:
                providers[matched] = min(prices)
            pending_provider = None
            continue
        if matched and not prices:
            pending_provider = matched
            continue
        if prices and pending_provider:
            price = min(prices)
            if pending_provider not in providers or price < providers[pending_provider]:
                providers[pending_provider] = price
            pending_provider = None
            continue
        if prices and i > 0:
            prev = _match_provider(lines[i - 1])
            if prev:
                price = min(prices)
                if prev not in providers or price < providers[prev]:
                    providers[prev] = price
    if not providers:
        prices = [int(x.replace(",", "")) for x in INR_PRICE_RE.findall(text)]
        prices = [p for p in prices if MIN_INR <= p <= 200_000]
        if not prices:
            for raw in USD_PRICE_RE.findall(text):
                try:
                    usd = float(raw.replace(",", ""))
                except ValueError:
                    continue
                if usd < MIN_USD:
                    continue
                p = int(round(usd * DEFAULT_USD_INR))
                if MIN_INR <= p <= 200_000:
                    prices.append(p)
        if prices:
            providers["Google Hotels"] = min(prices)
    return providers


def _fetch_night_google(
    page: Page,
    hotel: dict[str, str],
    cin: date,
    *,
    adults: int,
) -> DayPrice:
    url = _hotel_url(hotel, cin, adults=adults)
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(3500)
        dismiss_overlays(page)
        # Click into the matching hotel entity if search results shown
        name = hotel["name"]
        try:
            page.get_by_text(name, exact=False).first.click(timeout=4000)
            page.wait_for_timeout(2500)
            dismiss_overlays(page)
        except Exception:
            pass
        body = page.inner_text("body")
    except Exception as exc:
        log.debug("Google calendar night failed %s %s: %s", hotel["name"], cin, exc)
        return DayPrice(date=cin.isoformat(), lowest_price_inr=None)

    providers = _parse_ladder(body)
    if not providers:
        return DayPrice(date=cin.isoformat(), lowest_price_inr=None)
    best = min(providers, key=providers.get)  # type: ignore[arg-type]
    return DayPrice(
        date=cin.isoformat(),
        lowest_price_inr=providers[best],
        lowest_provider=f"Google/{best}",
        providers={f"Google/{k}": v for k, v in providers.items()},
    )


def enrich_calendar_with_google(
    calendar: HotelCalendar,
    hotel: dict[str, str],
    *,
    adults: int = 2,
    headless: bool = True,
    chunk_size: int = 8,
) -> HotelCalendar:
    """Merge Google Hotels mins into an existing Kayak calendar (take lower)."""
    nights = [date.fromisoformat(d.date) for d in calendar.days]
    google_by_date: dict[str, DayPrice] = {}
    i = 0
    while i < len(nights):
        chunk = nights[i : i + chunk_size]
        with browser_session(headless=headless) as (_p, _b, context):
            page = context.new_page()
            for cin in chunk:
                day = _fetch_night_google(page, hotel, cin, adults=adults)
                if day.lowest_price_inr is not None:
                    google_by_date[day.date] = day
                i += 1
                time.sleep(0.4)
        log.info(
            "Google enrich %s progress %d/%d (priced=%d)",
            hotel["name"],
            i,
            len(nights),
            len(google_by_date),
        )
        time.sleep(1.5)

    merged_days: list[DayPrice] = []
    for d in calendar.days:
        g = google_by_date.get(d.date)
        if g is None or g.lowest_price_inr is None:
            merged_days.append(d)
            continue
        providers = dict(d.providers or {})
        providers.update(g.providers or {})
        candidates = [(d.lowest_provider, d.lowest_price_inr)] if d.lowest_price_inr else []
        candidates.append((g.lowest_provider, g.lowest_price_inr))
        candidates = [(p, pr) for p, pr in candidates if pr is not None]
        best_prov, best_price = min(candidates, key=lambda x: x[1])
        merged_days.append(
            DayPrice(
                date=d.date,
                lowest_price_inr=best_price,
                lowest_provider=best_prov,
                providers=providers,
            )
        )
    return HotelCalendar(
        hotel=calendar.hotel,
        hid=calendar.hid,
        months=calendar.months,
        days=merged_days,
        details_base_url=calendar.details_base_url,
    )


def enrich_calendars_with_google(
    calendars: list[HotelCalendar],
    hotels: tuple[dict[str, str], ...] | list[dict[str, str]],
    *,
    adults: int = 2,
    headless: bool = True,
) -> list[HotelCalendar]:
    by_name = {h["name"]: h for h in hotels}
    out: list[HotelCalendar] = []
    for cal in calendars:
        hotel = by_name.get(cal.hotel)
        if not hotel:
            out.append(cal)
            continue
        log.info("=== Google enrich calendar %s ===", cal.hotel)
        out.append(
            enrich_calendar_with_google(
                cal, hotel, adults=adults, headless=headless
            )
        )
        time.sleep(2.0)
    return out
