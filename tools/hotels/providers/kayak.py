"""Kayak India hotel search — primary multi-OTA aggregator.

Intercepts `/i/api/search/dynamic/hotels/poll` JSON which includes per-provider
prices (Booking.com, Agoda, Expedia, brand sites, and others Kayak compares).
"""

from __future__ import annotations

import logging
import time
from typing import Any

from playwright.sync_api import BrowserContext, Page

from ..browser import dismiss_overlays, scroll_results
from ..models import HotelOffer, ProviderPrice, SearchQuery

log = logging.getLogger(__name__)

AREA_SLUGS = {
    "Madhapur": "Madhapur,Hyderabad,India",
    "Kondapur": "Kondapur,Hyderabad,India",
    "Gachibowli": "Gachibowli,Hyderabad,India",
}


def _search_url(query: SearchQuery) -> str:
    slug = AREA_SLUGS.get(query.area, f"{query.area},Hyderabad,India")
    # Multiple fs forms — Kayak accepts semicolon-separated star filters
    return (
        f"https://www.kayak.co.in/hotels/{slug}/"
        f"{query.check_in.isoformat()}/{query.check_out.isoformat()}/"
        f"{query.adults}adults"
        f"?sort=price_a&fs=stars={int(query.min_stars)};stars=5"
    )


def _dismiss_kayak_chrome(page: Page) -> None:
    dismiss_overlays(page)
    # Onboarding / compare-tool overlays commonly intercept clicks
    for sel in (
        'button[aria-label="Close"]',
        '[class*="c-ulo"] button',
        'button:has-text("Skip")',
        'button:has-text("Not now")',
        'button:has-text("No thanks")',
        '[data-testid="dialog-close"]',
    ):
        try:
            loc = page.locator(sel).first
            if loc.is_visible(timeout=500):
                loc.click(timeout=1000, force=True)
        except Exception:
            pass
    try:
        page.keyboard.press("Escape")
    except Exception:
        pass


def _stars_selected_in_poll(poll: dict[str, Any], min_stars: float) -> bool:
    """True if Kayak filterData indicates 4/5 star filters are selected."""
    stars = ((poll.get("filterData") or {}).get("stars") or {}).get("items") or []
    selected_ids = {str(i.get("id")) for i in stars if i.get("selected")}
    needed = {str(s) for s in range(int(min_stars), 6)}
    # Selected exactly the high-star buckets (not "0+" alone)
    return bool(selected_ids & needed) and "0" not in selected_ids


def _apply_star_filters(page: Page, min_stars: float) -> None:
    _dismiss_kayak_chrome(page)

    # Expand "Hotel class" / "Stars" section if collapsed
    for label in ("Hotel class", "Stars", "Star rating", "Class"):
        try:
            page.get_by_text(label, exact=False).first.click(timeout=1200, force=True)
            time.sleep(0.5)
        except Exception:
            pass

    # Smart filter chip
    for label in ("Class 4+", "4+", "4 stars and up"):
        try:
            loc = page.get_by_text(label, exact=True).first
            if loc.is_visible(timeout=800):
                loc.click(timeout=1500, force=True)
                time.sleep(2.0)
                return
        except Exception:
            pass

    # Individual star checkboxes
    for star in range(int(min_stars), 6):
        clicked = False
        for sel in (
            f'label:has-text("{star} stars")',
            f'label:has-text("{star}-star")',
            f'[aria-label="{star} stars"]',
            f'[aria-label*="{star} star"]',
        ):
            try:
                page.locator(sel).first.click(timeout=1000, force=True)
                clicked = True
                time.sleep(0.4)
                break
            except Exception:
                continue
        if not clicked:
            try:
                page.get_by_text(f"{star} stars", exact=False).first.click(timeout=1000, force=True)
                time.sleep(0.4)
            except Exception:
                pass


def _parse_poll_hotel(raw: dict[str, Any], query: SearchQuery) -> HotelOffer | None:
    if raw.get("resultType") != "core":
        return None
    stars = float(raw.get("stars") or 0)
    if stars < query.min_stars:
        return None
    name = (raw.get("localizedHotelName") or "").strip()
    if not name:
        return None

    providers: list[ProviderPrice] = []
    for p in raw.get("providers") or []:
        price_obj = p.get("price") or {}
        amount = price_obj.get("price")
        if amount is None:
            continue
        try:
            price_inr = int(round(float(amount)))
        except (TypeError, ValueError):
            continue
        if price_inr < 500 or price_inr > 200_000:
            continue
        providers.append(
            ProviderPrice(
                provider=p.get("localizedProviderName") or p.get("providerCode") or "Unknown",
                price_inr=price_inr,
                currency=price_obj.get("currency") or "INR",
                url=p.get("bookingUrl"),
                freebies=[
                    f.get("localizedName") or f.get("code")
                    for f in (p.get("freebies") or [])
                    if f.get("localizedName") or f.get("code")
                ],
            )
        )

    if not providers:
        return None

    best_by_provider: dict[str, ProviderPrice] = {}
    for pp in providers:
        key = pp.provider.lower()
        if key not in best_by_provider or pp.price_inr < best_by_provider[key].price_inr:
            best_by_provider[key] = pp
    providers = sorted(best_by_provider.values(), key=lambda x: x.price_inr)
    lowest = providers[0]

    rating = None
    review_count = None
    rating_obj = raw.get("rating") or {}
    if isinstance(rating_obj, dict):
        score = rating_obj.get("score") or rating_obj.get("value")
        if score is not None:
            try:
                rating = float(score)
            except (TypeError, ValueError):
                rating = None
        rc = rating_obj.get("reviewCount")
        if rc is not None:
            try:
                review_count = int(rc)
            except (TypeError, ValueError):
                review_count = None

    geo = raw.get("geolocation") or {}
    neighborhood = geo.get("localizedNeighborhoodName")

    details = raw.get("detailsUrl") or raw.get("url")
    if details and details.startswith("/"):
        details = "https://www.kayak.co.in" + details

    return HotelOffer(
        hotel=name,
        area=query.area,
        check_in=query.check_in,
        stars=stars,
        lowest_price_inr=lowest.price_inr,
        lowest_provider=lowest.provider,
        providers=providers,
        source="kayak",
        rating=rating,
        review_count=review_count,
        hotel_id=str(raw.get("hid") or raw.get("resultId") or ""),
        details_url=details,
        neighborhood=neighborhood,
    )


def fetch_kayak(context: BrowserContext, query: SearchQuery, *, max_wait_s: int = 40) -> list[HotelOffer]:
    page = context.new_page()
    polls: list[dict[str, Any]] = []

    def on_response(resp) -> None:
        try:
            if "/i/api/search/dynamic/hotels/poll" not in resp.url:
                return
            if resp.status != 200:
                return
            data = resp.json()
            if isinstance(data, dict) and "results" in data:
                polls.append(data)
        except Exception:
            return

    page.on("response", on_response)
    url = _search_url(query)
    log.info("Kayak fetch %s %s", query.area, query.check_in)
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60_000)
    except Exception as exc:
        log.warning("Kayak goto failed: %s", exc)
        page.close()
        return []

    _dismiss_kayak_chrome(page)

    deadline = time.time() + max_wait_s
    while time.time() < deadline:
        if any(p.get("status") in {"complete", "second-phase"} for p in polls):
            break
        time.sleep(0.4)

    poll_count_before = len(polls)
    _apply_star_filters(page, query.min_stars)
    _dismiss_kayak_chrome(page)

    # Wait for a post-filter poll if possible
    wait_until = time.time() + 12
    while time.time() < wait_until:
        if len(polls) > poll_count_before and any(
            _stars_selected_in_poll(p, query.min_stars) for p in polls[poll_count_before:]
        ):
            break
        time.sleep(0.5)

    # Infinite scroll / show more to pull additional result pages
    scroll_results(page, rounds=14, pause_s=1.0)
    time.sleep(1.5)

    by_id: dict[str, dict[str, Any]] = {}
    for poll in polls:
        for raw in poll.get("results") or []:
            if raw.get("resultType") != "core":
                continue
            hid = str(raw.get("hid") or raw.get("resultId") or "")
            if not hid:
                continue
            prev = by_id.get(hid)
            if prev is None or len(raw.get("providers") or []) >= len(prev.get("providers") or []):
                by_id[hid] = raw

    offers: list[HotelOffer] = []
    for raw in by_id.values():
        offer = _parse_poll_hotel(raw, query)
        if offer:
            offers.append(offer)

    provider_names = sorted(
        {p.provider for o in offers for p in o.providers}
    )
    log.info(
        "Kayak %s %s -> %d offers (polls=%d raw=%d otas=%s)",
        query.area,
        query.check_in,
        len(offers),
        len(polls),
        len(by_id),
        provider_names,
    )
    page.close()
    return offers
