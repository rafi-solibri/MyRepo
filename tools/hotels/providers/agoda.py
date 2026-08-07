"""Agoda search — DOM scrape of property cards."""

from __future__ import annotations

import logging
import re
import time
from urllib.parse import quote

from playwright.sync_api import BrowserContext

from ..browser import dismiss_overlays, scroll_results
from ..models import HotelOffer, ProviderPrice, SearchQuery

log = logging.getLogger(__name__)
PRICE_RE = re.compile(r"(?:₹|Rs\.?|INR|\$)\s*([\d,]+)", re.I)

# Agoda city id for Hyderabad
HYD_CITY_ID = 12454


def _url(query: SearchQuery) -> str:
    return (
        "https://www.agoda.com/search"
        f"?city={HYD_CITY_ID}"
        f"&checkIn={query.check_in.isoformat()}"
        f"&checkOut={query.check_out.isoformat()}"
        f"&rooms={query.rooms}&adults={query.adults}&children=0"
        f"&priceCur=INR&los=1"
        f"&textToSearch={quote(query.area)}"
        f"&starRating={int(query.min_stars)},5"
    )


def fetch_agoda(context: BrowserContext, query: SearchQuery) -> list[HotelOffer]:
    page = context.new_page()
    log.info("Agoda fetch %s %s", query.area, query.check_in)
    try:
        page.goto(_url(query), wait_until="domcontentloaded", timeout=70_000)
    except Exception as exc:
        log.warning("Agoda goto failed: %s", exc)
        page.close()
        return []

    dismiss_overlays(page)
    # Cookie / search CTA
    for sel in (
        'button:has-text("Dismiss")',
        'button:has-text("SEARCH")',
        'button[data-selenium="searchButton"]',
        'button:has-text("Search")',
    ):
        try:
            page.locator(sel).first.click(timeout=2000, force=True)
            time.sleep(1.0)
        except Exception:
            pass
    time.sleep(6)
    scroll_results(page, rounds=8, pause_s=1.0)

    offers: list[HotelOffer] = []
    cards = page.locator(
        '[data-selenium="hotel-item"], li[data-selenium="hotel-item"], '
        'ol[class*="hotel-list"] li, div[data-element-name="property-card"]'
    )
    count = cards.count()
    if count == 0:
        # broader fallback
        cards = page.locator('a[href*="/hotel/"]')
        count = min(cards.count(), 100)

    seen: set[str] = set()
    for i in range(min(count, 80)):
        card = cards.nth(i)
        try:
            text = card.inner_text(timeout=1500)
        except Exception:
            continue
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if not lines:
            continue
        name = lines[0]
        if name.lower() in seen or len(name) < 3:
            continue
        prices = [int(p.replace(",", "")) for p in PRICE_RE.findall(text)]
        # Agoda may show USD briefly; skip tiny dollar-looking amounts under 100 if currency ambiguous
        prices = [p for p in prices if 800 <= p <= 200_000]
        if not prices:
            continue
        stars = query.min_stars
        m = re.search(r"(\d(?:\.\d)?)\s*(?:star|★)", text, re.I)
        if m:
            stars = float(m.group(1))
        if stars < query.min_stars:
            continue
        price = min(prices)
        seen.add(name.lower())
        offers.append(
            HotelOffer(
                hotel=name,
                area=query.area,
                check_in=query.check_in,
                stars=stars,
                lowest_price_inr=price,
                lowest_provider="Agoda",
                providers=[ProviderPrice(provider="Agoda", price_inr=price)],
                source="agoda",
            )
        )

    log.info("Agoda %s %s -> %d offers", query.area, query.check_in, len(offers))
    page.close()
    return offers
