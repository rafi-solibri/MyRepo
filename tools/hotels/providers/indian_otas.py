"""Best-effort scrapers for MakeMyTrip / Goibibo / Cleartrip / EaseMyTrip / Yatra.

These sites often block cloud/datacenter IPs (HTTP/2 errors, bot walls). We still
attempt fetches with HTTP/1.1 disabled-http2 Chromium; failures return [].
"""

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


def _parse_cards(page, query: SearchQuery, provider: str, selectors: str) -> list[HotelOffer]:
    offers: list[HotelOffer] = []
    cards = page.locator(selectors)
    seen: set[str] = set()
    for i in range(min(cards.count(), 60)):
        card = cards.nth(i)
        try:
            text = card.inner_text(timeout=1200)
        except Exception:
            continue
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if not lines:
            continue
        name = lines[0]
        if name.lower() in seen or len(name) < 3:
            continue
        prices = [int(p.replace(",", "")) for p in PRICE_RE.findall(text)]
        prices = [p for p in prices if 800 <= p <= 200_000]
        if not prices:
            continue
        stars = query.min_stars
        m = re.search(r"(\d(?:\.\d)?)\s*(?:star|★)", text, re.I)
        if m:
            stars = float(m.group(1))
        # Many Indian OTAs put star in icons only — keep if filter UI applied
        if stars < query.min_stars and ("star" in text.lower() or "★" in text):
            continue
        if stars < query.min_stars:
            stars = query.min_stars
        price = min(prices)
        seen.add(name.lower())
        offers.append(
            HotelOffer(
                hotel=name,
                area=query.area,
                check_in=query.check_in,
                stars=stars,
                lowest_price_inr=price,
                lowest_provider=provider,
                providers=[ProviderPrice(provider=provider, price_inr=price)],
                source=provider.lower().replace(" ", "_"),
            )
        )
    return offers


def _try_goto(page, url: str, timeout_ms: int = 25_000) -> bool:
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        return True
    except Exception as exc:
        log.warning("Goto failed %s: %s", url[:80], exc)
        return False


def fetch_makemytrip(context: BrowserContext, query: SearchQuery) -> list[HotelOffer]:
    page = context.new_page()
    cin = query.check_in.strftime("%m%d%Y")
    cout = query.check_out.strftime("%m%d%Y")
    url = (
        "https://www.makemytrip.com/hotels/hotel-listing/"
        f"?checkin={cin}&checkout={cout}&city=CTHYD"
        f"&roomStayQualifier={query.adults}e0e&locusId=CTHYD&country=IN"
        f"&locusType=city&searchText={quote(query.area)}&rsc=1e{query.adults}e0e"
    )
    log.info("MakeMyTrip fetch %s %s", query.area, query.check_in)
    if not _try_goto(page, url):
        page.close()
        return []
    dismiss_overlays(page)
    time.sleep(6)
    scroll_results(page, rounds=5)
    offers = _parse_cards(
        page,
        query,
        "MakeMyTrip",
        '#listing-card, div[id*="ListingCard"], div[class*="listingCard"], '
        'div[data-testid="listingCard"], a[id*="htl_id"]',
    )
    log.info("MakeMyTrip %s %s -> %d", query.area, query.check_in, len(offers))
    page.close()
    return offers


def fetch_goibibo(context: BrowserContext, query: SearchQuery) -> list[HotelOffer]:
    page = context.new_page()
    url = (
        "https://www.goibibo.com/hotels/hotels-in-hyderabad-ct/"
        f"?checkin={query.check_in.isoformat()}&checkout={query.check_out.isoformat()}"
        f"&rooms={query.rooms}&adults={query.adults}&cityName={quote(query.area)}"
    )
    log.info("Goibibo fetch %s %s", query.area, query.check_in)
    if not _try_goto(page, url):
        page.close()
        return []
    dismiss_overlays(page)
    time.sleep(5)
    scroll_results(page, rounds=5)
    offers = _parse_cards(
        page,
        query,
        "Goibibo",
        'div[class*="HotelCard"], div[data-testid="hotel-card"], a[href*="/hotels/"]',
    )
    log.info("Goibibo %s %s -> %d", query.area, query.check_in, len(offers))
    page.close()
    return offers


def fetch_cleartrip(context: BrowserContext, query: SearchQuery) -> list[HotelOffer]:
    page = context.new_page()
    url = (
        "https://www.cleartrip.com/hotels/results/hyderabad"
        f"?city=Hyderabad&state=Telangana&country=IN"
        f"&chk_in={query.check_in.isoformat()}&chk_out={query.check_out.isoformat()}"
        f"&num_rooms={query.rooms}&adults={query.adults}&children=0"
        f"&area={quote(query.area)}"
    )
    log.info("Cleartrip fetch %s %s", query.area, query.check_in)
    if not _try_goto(page, url):
        page.close()
        return []
    dismiss_overlays(page)
    time.sleep(5)
    scroll_results(page, rounds=5)
    offers = _parse_cards(
        page,
        query,
        "Cleartrip",
        'div[class*="HotelCard"], article, a[href*="/hotels/"]',
    )
    log.info("Cleartrip %s %s -> %d", query.area, query.check_in, len(offers))
    page.close()
    return offers


def fetch_easemytrip(context: BrowserContext, query: SearchQuery) -> list[HotelOffer]:
    page = context.new_page()
    url = (
        f"https://www.easemytrip.com/hotels/hotels-in-{query.area.lower()}.html"
        f"?city={quote(query.area)}&chkIn={query.check_in.isoformat()}"
        f"&chkOut={query.check_out.isoformat()}&numRooms={query.rooms}"
        f"&adults={query.adults}&children=0"
    )
    log.info("EaseMyTrip fetch %s %s", query.area, query.check_in)
    if not _try_goto(page, url):
        page.close()
        return []
    dismiss_overlays(page)
    time.sleep(5)
    scroll_results(page, rounds=5)
    offers = _parse_cards(
        page,
        query,
        "EaseMyTrip",
        'div[class*="hotel"], div[id*="hotel"], a[href*="/hotels/"]',
    )
    log.info("EaseMyTrip %s %s -> %d", query.area, query.check_in, len(offers))
    page.close()
    return offers


def fetch_yatra(context: BrowserContext, query: SearchQuery) -> list[HotelOffer]:
    page = context.new_page()
    url = (
        "https://hotel.yatra.com/hotel-search/dom/search"
        f"?checkoutDate={query.check_out.isoformat()}"
        f"&checkinDate={query.check_in.isoformat()}"
        f"&roomRequests[0].id=1&roomRequests[0].noOfAdults={query.adults}"
        f"&roomRequests[0].noOfChildren=0&tenant=B2C"
        f"&city.name={quote(query.area)}&city.code={quote(query.area)}"
    )
    log.info("Yatra fetch %s %s", query.area, query.check_in)
    if not _try_goto(page, url):
        page.close()
        return []
    dismiss_overlays(page)
    time.sleep(5)
    scroll_results(page, rounds=5)
    offers = _parse_cards(
        page,
        query,
        "Yatra",
        'div[class*="hotel"], li[class*="hotel"], a[href*="hotel"]',
    )
    log.info("Yatra %s %s -> %d", query.area, query.check_in, len(offers))
    page.close()
    return offers
