"""Hotels.com / Expedia family — useful when Indian OTAs block cloud IPs."""

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


def _url(query: SearchQuery) -> str:
    dest = quote(f"{query.area}, Hyderabad, Telangana, India")
    return (
        "https://www.hotels.com/Hotel-Search"
        f"?destination={dest}"
        f"&startDate={query.check_in.isoformat()}"
        f"&endDate={query.check_out.isoformat()}"
        f"&rooms={query.rooms}&adults={query.adults}"
        f"&star={int(query.min_stars)}&sort=PRICE_LOW_TO_HIGH"
    )


def fetch_hotels_com(context: BrowserContext, query: SearchQuery) -> list[HotelOffer]:
    page = context.new_page()
    log.info("Hotels.com fetch %s %s", query.area, query.check_in)
    try:
        page.goto(_url(query), wait_until="domcontentloaded", timeout=30_000)
    except Exception as exc:
        log.warning("Hotels.com goto failed: %s", exc)
        page.close()
        return []

    dismiss_overlays(page)
    time.sleep(5)
    scroll_results(page, rounds=6, pause_s=0.9)

    offers: list[HotelOffer] = []
    cards = page.locator(
        '[data-stid="property-listing"], section[class*="PropertyListing"], '
        'div[data-test-id="property-card"], a[href*="/ho"]'
    )
    seen: set[str] = set()
    for i in range(min(cards.count(), 80)):
        card = cards.nth(i)
        try:
            text = card.inner_text(timeout=1200)
        except Exception:
            continue
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if not lines:
            continue
        name = lines[0]
        if name.lower() in seen or len(name) < 3 or len(name) > 90:
            continue
        prices = [int(p.replace(",", "")) for p in PRICE_RE.findall(text)]
        prices = [p for p in prices if 800 <= p <= 200_000]
        if not prices:
            continue
        stars = query.min_stars
        m = re.search(r"(\d(?:\.\d)?)\s*(?:star|out of 5)", text, re.I)
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
                lowest_provider="Hotels.com",
                providers=[ProviderPrice(provider="Hotels.com", price_inr=price)],
                source="hotels_com",
            )
        )

    log.info("Hotels.com %s %s -> %d offers", query.area, query.check_in, len(offers))
    page.close()
    return offers
