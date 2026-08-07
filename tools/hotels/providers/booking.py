"""Booking.com search — direct OTA prices via DOM + embedded JSON."""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any
from urllib.parse import quote

from playwright.sync_api import BrowserContext

from ..browser import dismiss_overlays, scroll_results
from ..models import HotelOffer, ProviderPrice, SearchQuery

log = logging.getLogger(__name__)

PRICE_RE = re.compile(r"(?:₹|Rs\.?|INR)\s*([\d,]+)", re.I)


def _url(query: SearchQuery) -> str:
    ss = quote(f"{query.area}, Hyderabad")
    nflt = "class%3D4%3Bclass%3D5" if query.min_stars >= 4 else ""
    return (
        "https://www.booking.com/searchresults.en-gb.html"
        f"?ss={ss}&checkin={query.check_in.isoformat()}"
        f"&checkout={query.check_out.isoformat()}"
        f"&group_adults={query.adults}&no_rooms={query.rooms}"
        f"&selected_currency=INR&nflt={nflt}"
    )


def _offers_from_dom(page, query: SearchQuery) -> list[HotelOffer]:
    offers: list[HotelOffer] = []
    cards = page.locator('[data-testid="property-card"], div[data-testid="property-card"]')
    count = cards.count()
    for i in range(min(count, 80)):
        card = cards.nth(i)
        try:
            text = card.inner_text(timeout=2000)
        except Exception:
            continue
        name = None
        try:
            name = card.locator('[data-testid="title"]').first.inner_text(timeout=800).strip()
        except Exception:
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            name = lines[0] if lines else None
        if not name:
            continue

        stars = query.min_stars
        try:
            aria = card.locator('[data-testid="rating-stars"], [aria-label*="out of 5"]').first.get_attribute(
                "aria-label", timeout=500
            )
            if aria:
                m = re.search(r"(\d+(?:\.\d+)?)", aria)
                if m:
                    stars = float(m.group(1))
        except Exception:
            # fallback: look for "4-star" in text
            m = re.search(r"(\d)\s*[- ]?star", text, re.I)
            if m:
                stars = float(m.group(1))

        if stars < query.min_stars:
            continue

        prices = [int(p.replace(",", "")) for p in PRICE_RE.findall(text)]
        prices = [p for p in prices if 800 <= p <= 200_000]
        if not prices:
            continue
        price = min(prices)
        offers.append(
            HotelOffer(
                hotel=name,
                area=query.area,
                check_in=query.check_in,
                stars=stars,
                lowest_price_inr=price,
                lowest_provider="Booking.com",
                providers=[ProviderPrice(provider="Booking.com", price_inr=price)],
                source="booking",
            )
        )
    return offers


def fetch_booking(context: BrowserContext, query: SearchQuery) -> list[HotelOffer]:
    page = context.new_page()
    graphql_blobs: list[dict[str, Any]] = []

    def on_response(resp) -> None:
        try:
            if "dml/graphql" not in resp.url or resp.status != 200:
                return
            data = resp.json()
            text = json.dumps(data)
            if "price" in text.lower() and (
                "property" in text.lower() or "hotel" in text.lower() or "card" in text.lower()
            ):
                graphql_blobs.append(data)
        except Exception:
            return

    page.on("response", on_response)
    log.info("Booking.com fetch %s %s", query.area, query.check_in)
    try:
        page.goto(_url(query), wait_until="domcontentloaded", timeout=70_000)
    except Exception as exc:
        log.warning("Booking goto failed: %s", exc)
        page.close()
        return []

    dismiss_overlays(page)
    # captcha / robot page detection
    body = ""
    try:
        body = page.inner_text("body")[:2000]
    except Exception:
        pass
    if "JavaScript is disabled" in body or "not a robot" in body.lower():
        log.warning("Booking.com bot check / JS challenge — DOM scrape may be empty")

    time.sleep(4)
    scroll_results(page, rounds=6, pause_s=0.8)
    offers = _offers_from_dom(page, query)
    log.info("Booking.com %s %s -> %d offers (graphql=%d)", query.area, query.check_in, len(offers), len(graphql_blobs))
    page.close()
    return offers
