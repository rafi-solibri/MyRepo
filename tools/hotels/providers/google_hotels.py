"""Google Hotels — aggregates many OTAs; scrape visible deal cards."""

from __future__ import annotations

import logging
import re
import time
from urllib.parse import quote

from playwright.sync_api import BrowserContext

from ..browser import dismiss_overlays, scroll_results
from ..models import HotelOffer, ProviderPrice, SearchQuery

log = logging.getLogger(__name__)
PRICE_RE = re.compile(r"(?:₹|Rs\.?|INR)\s*([\d,]+)", re.I)


def _url(query: SearchQuery) -> str:
    q = quote(f"{query.area} Hyderabad hotels")
    # Google Travel date format YYYY-MM-DD works in many locales via query params
    return (
        "https://www.google.com/travel/hotels/"
        f"{quote(query.area)}"
        f"?q={q}"
        f"&dates={query.check_in.isoformat().replace('-', '')},"
        f"{query.check_out.isoformat().replace('-', '')}"
        f"&adults={query.adults}&hl=en-IN&gl=in&curr=INR"
    )


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
    # Try open filters for 4+ stars
    for label in ("4 or more", "4-star", "4 stars", "Star rating"):
        try:
            page.get_by_text(label, exact=False).first.click(timeout=1500)
            time.sleep(1)
        except Exception:
            pass

    scroll_results(page, rounds=8, pause_s=0.9)

    offers: list[HotelOffer] = []
    # Google Travel hotel cards vary; parse dense text blocks with prices
    try:
        body = page.inner_text("body")
    except Exception:
        body = ""

    # Heuristic: lines with hotel-ish names near prices are noisy; prefer card locators
    cards = page.locator('a[href*="/travel/hotels/entity"], div[role="listitem"], c-wiz div[jscontroller]')
    seen: set[str] = set()
    count = min(cards.count(), 120)
    for i in range(count):
        card = cards.nth(i)
        try:
            text = card.inner_text(timeout=1000)
        except Exception:
            continue
        if len(text) < 20 or "₹" not in text and "Rs" not in text:
            continue
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if not lines:
            continue
        name = lines[0]
        if name.lower() in seen or len(name) < 4 or len(name) > 80:
            continue
        if name.lower().startswith(("filter", "price", "sort", "map", "search", "sign")):
            continue
        prices = [int(p.replace(",", "")) for p in PRICE_RE.findall(text)]
        prices = [p for p in prices if 800 <= p <= 200_000]
        if not prices:
            continue
        stars = query.min_stars
        m = re.search(r"(\d(?:\.\d)?)\s*(?:star|★|⭐)", text, re.I)
        if m:
            stars = float(m.group(1))
        if stars < query.min_stars:
            # Google often omits star text; keep if user asked 4+ and card survived filter UI
            if "star" in text.lower() or "★" in text:
                continue
            stars = query.min_stars
        price = min(prices)
        seen.add(name.lower())
        # Provider line sometimes includes "on Booking.com" / "MakeMyTrip"
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
