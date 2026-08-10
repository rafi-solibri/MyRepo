"""Google Hotels — aggregates many OTAs; scrape visible deal cards.

Cloud Google often renders USD even with gl=in&curr=INR; convert those
amounts to INR so inventory is not empty when ₹ is absent.
"""

from __future__ import annotations

import logging
import os
import re
import time
from urllib.parse import quote

from playwright.sync_api import BrowserContext

from ..browser import dismiss_overlays, scroll_results
from ..models import HotelOffer, ProviderPrice, SearchQuery

log = logging.getLogger(__name__)

# Approximate FX for cloud locales that show $ instead of ₹.
DEFAULT_USD_INR = float(os.environ.get("HOTEL_USD_INR", "87"))

INR_PRICE_RE = re.compile(r"(?:₹|Rs\.?|INR)\s*([\d,]+)", re.I)
USD_PRICE_RE = re.compile(r"\$\s*([\d,]+(?:\.\d{1,2})?)")

# UI chrome that must not be treated as hotel names.
_SKIP_NAME_PREFIXES = (
    "filter",
    "price",
    "sort",
    "map",
    "search",
    "sign",
    "deals",
    "offers",
    "results",
    "guest",
    "rating",
    "amenities",
    "cancellation",
    "popular",
    "all filters",
    "clear",
    "apply",
)


def _url(query: SearchQuery) -> str:
    q = quote(f"{query.area} Hyderabad hotels")
    return (
        "https://www.google.com/travel/hotels/"
        f"{quote(query.area)}"
        f"?q={q}"
        f"&dates={query.check_in.isoformat().replace('-', '')},"
        f"{query.check_out.isoformat().replace('-', '')}"
        f"&adults={query.adults}&hl=en-IN&gl=in&curr=INR"
    )


# Nightly hotel floors — reject UI crumbs like "$7" taxes/fees (~₹609).
MIN_INR = 1_000
MIN_USD = 12.0


def _prices_from_text(text: str) -> list[int]:
    """Extract nightly prices in INR from card text (₹ or $)."""
    prices: list[int] = []
    for raw in INR_PRICE_RE.findall(text):
        try:
            p = int(raw.replace(",", ""))
        except ValueError:
            continue
        if MIN_INR <= p <= 200_000:
            prices.append(p)
    if prices:
        return prices
    for raw in USD_PRICE_RE.findall(text):
        try:
            usd = float(raw.replace(",", ""))
        except ValueError:
            continue
        if usd < MIN_USD:
            continue
        inr = int(round(usd * DEFAULT_USD_INR))
        if MIN_INR <= inr <= 200_000:
            prices.append(inr)
    return prices


def _is_ui_chip(name: str) -> bool:
    low = name.lower().strip()
    if not low or len(low) < 4 or len(low) > 80:
        return True
    return any(low.startswith(p) for p in _SKIP_NAME_PREFIXES)


def fetch_google_hotels(context: BrowserContext, query: SearchQuery) -> list[HotelOffer]:
    page = context.new_page()
    log.info("Google Hotels fetch %s %s", query.area, query.check_in)
    try:
        page.goto(_url(query), wait_until="domcontentloaded", timeout=70_000)
    except Exception as exc:
        log.warning("Google Hotels goto failed: %s", exc)
        page.close()
        return []

    dismiss_overlays(page)
    time.sleep(5)
    for label in ("4 or more", "4-star", "4 stars", "Star rating"):
        try:
            page.get_by_text(label, exact=False).first.click(timeout=1500)
            time.sleep(1)
        except Exception:
            pass

    scroll_results(page, rounds=8, pause_s=0.9)

    offers: list[HotelOffer] = []
    cards = page.locator(
        'a[href*="/travel/hotels/entity"], div[role="listitem"], c-wiz div[jscontroller]'
    )
    seen: set[str] = set()
    count = min(cards.count(), 120)
    for i in range(count):
        card = cards.nth(i)
        try:
            text = card.inner_text(timeout=1000)
        except Exception:
            continue
        if len(text) < 20:
            continue
        if "₹" not in text and "Rs" not in text and "$" not in text:
            continue
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if not lines:
            continue
        name = lines[0]
        if name.lower() in seen or _is_ui_chip(name):
            continue
        prices = _prices_from_text(text)
        if not prices:
            continue
        stars = query.min_stars
        m = re.search(r"(\d(?:\.\d)?)\s*(?:star|★|⭐)", text, re.I)
        if m:
            stars = float(m.group(1))
        if stars < query.min_stars:
            if "star" in text.lower() or "★" in text:
                continue
            stars = query.min_stars
        price = min(prices)
        seen.add(name.lower())
        provider = "Google Hotels"
        for candidate in (
            "MakeMyTrip",
            "Booking.com",
            "Agoda",
            "Cleartrip",
            "EaseMyTrip",
            "Yatra",
            "Goibibo",
            "Hotels.com",
            "Expedia",
        ):
            if candidate.lower() in text.lower():
                provider = candidate
                break
        offers.append(
            HotelOffer(
                hotel=name,
                area=query.area,
                check_in=query.check_in,
                stars=stars,
                lowest_price_inr=price,
                lowest_provider=provider,
                providers=[ProviderPrice(provider=provider, price_inr=price)],
                source="google",
            )
        )

    log.info("Google Hotels %s %s -> %d offers", query.area, query.check_in, len(offers))
    page.close()
    return offers
