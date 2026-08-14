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


BARE_GOOGLE_KEYS = frozenset({"Google Hotels", "Google/Google Hotels"})


def _is_bare_google_key(key: str) -> bool:
    return key in BARE_GOOGLE_KEYS


def merge_google_day(kayak: DayPrice, google: DayPrice | None) -> DayPrice:
    """Merge Google Hotels into a Kayak calendar day.

    Unlabeled page-min ("Google/Google Hotels") must not undercut real Kayak
    OTA prices — cloud Google pages often expose $12 "GREAT PRICE" chips.
    Named Google OTAs (Google/Agoda, …) still win when they are cheaper and
    pass the nightly floor.
    """
    if google is None or google.lowest_price_inr is None:
        return kayak

    providers = dict(kayak.providers or {})
    kayak_has = kayak.lowest_price_inr is not None
    for key, price in (google.providers or {}).items():
        if price is None or price < MIN_INR:
            continue
        if _is_bare_google_key(key) and kayak_has:
            continue
        if key in providers:
            providers[key] = min(providers[key], price)
        else:
            providers[key] = price

    if not providers:
        if not kayak_has and google.lowest_price_inr >= MIN_INR and not _is_bare_google_key(
            google.lowest_provider or ""
        ):
            return google
        if not kayak_has and google.lowest_price_inr >= MIN_INR:
            # Bare Google is better than an empty cell, but only at the floor.
            return DayPrice(
                date=kayak.date,
                lowest_price_inr=google.lowest_price_inr,
                lowest_provider=google.lowest_provider,
                providers=dict(google.providers or {}),
            )
        return kayak

    best_name = min(providers, key=providers.get)  # type: ignore[arg-type]
    return DayPrice(
        date=kayak.date,
        lowest_price_inr=providers[best_name],
        lowest_provider=best_name,
        providers=providers,
    )


def strip_untrusted_google_from_calendar(calendar: HotelCalendar) -> HotelCalendar:
    """Re-apply merge rules to an already-enriched calendar (no re-fetch)."""
    days: list[DayPrice] = []
    for d in calendar.days:
        kayak_providers = {
            k: v
            for k, v in (d.providers or {}).items()
            if not str(k).startswith("Google")
        }
        google_providers = {
            k: v
            for k, v in (d.providers or {}).items()
            if str(k).startswith("Google")
        }
        kayak_day = DayPrice(
            date=d.date,
            lowest_price_inr=min(kayak_providers.values()) if kayak_providers else None,
            lowest_provider=(
                min(kayak_providers, key=kayak_providers.get) if kayak_providers else None  # type: ignore[arg-type]
            ),
            providers=kayak_providers,
        )
        google_day = None
        if google_providers:
            best = min(google_providers, key=google_providers.get)  # type: ignore[arg-type]
            google_day = DayPrice(
                date=d.date,
                lowest_price_inr=google_providers[best],
                lowest_provider=best,
                providers=google_providers,
            )
        days.append(merge_google_day(kayak_day, google_day))
    return HotelCalendar(
        hotel=calendar.hotel,
        hid=calendar.hid,
        months=calendar.months,
        days=days,
        details_base_url=calendar.details_base_url,
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
        merged_days.append(merge_google_day(d, google_by_date.get(d.date)))
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
