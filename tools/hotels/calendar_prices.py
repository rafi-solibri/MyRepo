"""Per-night lowest multi-OTA prices for tracked hotels (calendar view).

Uses Kayak hotel rates API (`/i/api/search/dynamic/hotels/rates`) which returns
Booking.com / Agoda / Expedia / etc. for a given night; we keep the minimum.
"""

from __future__ import annotations

import calendar as cal
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from typing import Any

from playwright.sync_api import BrowserContext, Page

from .browser import browser_session

log = logging.getLogger(__name__)

# Most-important tracked hotels for calendar view
TRACKED_HOTELS: tuple[dict[str, str], ...] = (
    {
        "name": "Hotel Qualia Oak",
        "hid": "1073114832",
        "slug": "Hyderabad-p15297-h1073114832",
        "google_query": "Hotel Qualia Oak Madhapur Hyderabad",
    },
    {
        "name": "Oak Business Hotel",
        "hid": "1071537171",
        "slug": "Hyderabad-p15297-h1071537171",
        "google_query": "Oak Business Hotel Madhapur Hyderabad",
    },
)


@dataclass
class DayPrice:
    date: str
    lowest_price_inr: int | None
    lowest_provider: str | None = None
    providers: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HotelCalendar:
    hotel: str
    hid: str
    months: list[str]  # YYYY-MM
    days: list[DayPrice]
    details_base_url: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "hotel": self.hotel,
            "hid": self.hid,
            "months": self.months,
            "days": [d.to_dict() for d in self.days],
            "details_base_url": self.details_base_url,
        }


def _month_start(year: int, month: int) -> date:
    return date(year, month, 1)


def _add_month(year: int, month: int, delta: int = 1) -> tuple[int, int]:
    month += delta
    while month > 12:
        month -= 12
        year += 1
    while month < 1:
        month += 12
        year -= 1
    return year, month


def calendar_month_range(today: date | None = None) -> list[tuple[int, int]]:
    """Current calendar month + next month."""
    today = today or date.today()
    y2, m2 = _add_month(today.year, today.month, 1)
    return [(today.year, today.month), (y2, m2)]


def nights_for_months(months: list[tuple[int, int]], *, today: date | None = None) -> list[date]:
    """Bookable nights in the given months (check-in today or later)."""
    today = today or date.today()
    out: list[date] = []
    for year, month in months:
        last = cal.monthrange(year, month)[1]
        for day in range(1, last + 1):
            d = date(year, month, day)
            if d < today:
                continue
            out.append(d)
    return out


def _detail_url(hotel: dict[str, str], cin: date) -> str:
    cout = cin + timedelta(days=1)
    return (
        f"https://www.kayak.co.in/hotels/{hotel['slug']}-details/"
        f"{cin.isoformat()}/{cout.isoformat()}/2adults"
    )


def _seed_and_csrf(page: Page, hotel: dict[str, str], seed_night: date) -> str | None:
    csrf_box: dict[str, str | None] = {"v": None}

    def on_req(req) -> None:
        if "/hotels/rates" in req.url and req.headers.get("x-csrf"):
            csrf_box["v"] = req.headers["x-csrf"]

    page.on("request", on_req)
    url = _detail_url(hotel, seed_night)
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(4500)
        if "/security/check" in (page.url or ""):
            log.warning("Kayak security check on seed for %s — retry once", hotel["name"])
            page.wait_for_timeout(2000)
            page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(4500)
    except Exception as exc:
        log.warning("Seed goto failed for %s: %s", hotel["name"], exc)
    page.remove_listener("request", on_req)
    return csrf_box["v"]


def _price_via_navigation(page: Page, hotel: dict[str, str], cin: date) -> tuple[int | None, str | None, dict[str, int], str | None]:
    """Fallback: load detail page and intercept rates JSON. Returns csrf if seen."""
    csrf: str | None = None
    captured: dict[str, Any] = {}

    def on_req(req) -> None:
        nonlocal csrf
        if "/hotels/rates" in req.url and req.headers.get("x-csrf"):
            csrf = req.headers["x-csrf"]

    def on_resp(resp) -> None:
        if "/hotels/rates" in resp.url and resp.status == 200:
            try:
                captured["data"] = resp.json()
            except Exception:
                pass

    page.on("request", on_req)
    page.on("response", on_resp)
    try:
        with page.expect_response(
            lambda r: "/hotels/rates" in r.url and r.status == 200, timeout=25_000
        ) as resp_info:
            page.goto(_detail_url(hotel, cin), wait_until="commit", timeout=30_000)
        try:
            captured["data"] = resp_info.value.json()
        except Exception:
            pass
    except Exception as exc:
        log.debug("nav rates miss %s %s: %s", hotel["name"], cin, exc)
        page.wait_for_timeout(2000)
    page.remove_listener("request", on_req)
    page.remove_listener("response", on_resp)
    if "data" in captured:
        price, prov, providers = _parse_rates_json(captured["data"])
        return price, prov, providers, csrf
    return None, None, {}, csrf


def _parse_rates_json(data: dict[str, Any]) -> tuple[int | None, str | None, dict[str, int]]:
    providers: dict[str, int] = {}
    for g in data.get("groups") or []:
        for row in g.get("rows") or []:
            for opt in row.get("bookingOptions") or []:
                amount = (opt.get("price") or {}).get("price")
                if amount is None:
                    continue
                try:
                    price = int(round(float(amount)))
                except (TypeError, ValueError):
                    continue
                if price < 500 or price > 200_000:
                    continue
                name = opt.get("localizedProviderName") or opt.get("providerCode") or "Unknown"
                if name not in providers or price < providers[name]:
                    providers[name] = price
    if not providers:
        sel = data.get("selectedBookingOption") or {}
        amount = (sel.get("price") or {}).get("price")
        if amount is not None:
            try:
                price = int(round(float(amount)))
                name = sel.get("localizedProviderName") or "Unknown"
                providers[name] = price
            except (TypeError, ValueError):
                pass
    if not providers:
        return None, None, {}
    best_name = min(providers, key=providers.get)  # type: ignore[arg-type]
    return providers[best_name], best_name, providers


def _fetch_night(
    page: Page,
    hotel: dict[str, str],
    cin: date,
    csrf: str | None,
    *,
    adults: int,
) -> tuple[DayPrice, str | None]:
    """Fetch one night; returns (DayPrice, updated_csrf)."""
    cout = cin + timedelta(days=1)
    api = (
        "https://www.kayak.co.in/i/api/search/dynamic/hotels/rates"
        f"?hid={hotel['hid']}&checkin={cin.isoformat()}&checkout={cout.isoformat()}"
        f"&rooms=1&adults={adults}&childAges=&priceMode=nightly-total"
    )
    referer = _detail_url(hotel, cin)
    price = None
    provider = None
    providers: dict[str, int] = {}
    try:
        resp = page.request.get(
            api,
            headers={
                "x-csrf": csrf or "",
                "x-requested-with": "XMLHttpRequest",
                "accept": "application/json",
                "referer": referer,
            },
            timeout=25_000,
        )
        if resp.status == 200:
            price, provider, providers = _parse_rates_json(resp.json())
        elif resp.status in (401, 403):
            return (
                DayPrice(date=cin.isoformat(), lowest_price_inr=None),
                None,  # signal caller to rotate session
            )
        else:
            log.debug("rates %s %s -> HTTP %s", hotel["name"], cin, resp.status)
    except Exception:
        log.exception("rates failed %s %s", hotel["name"], cin)
    return (
        DayPrice(
            date=cin.isoformat(),
            lowest_price_inr=price,
            lowest_provider=provider,
            providers=providers,
        ),
        csrf,
    )


def fetch_hotel_calendar(
    hotel: dict[str, str],
    nights: list[date],
    *,
    adults: int = 2,
    headless: bool = True,
    chunk_size: int = 10,
) -> HotelCalendar:
    """Fetch calendar nights; each chunk uses a brand-new browser (avoids Kayak 403)."""
    months = sorted({f"{d.year:04d}-{d.month:02d}" for d in nights})
    by_date: dict[str, DayPrice] = {}
    fail_counts: dict[str, int] = {}
    i = 0
    while i < len(nights):
        chunk = nights[i : i + chunk_size]
        with browser_session(headless=headless) as (_p, _b, context):
            page = context.new_page()
            csrf = _seed_and_csrf(page, hotel, chunk[0])
            if not csrf and len(chunk) > 1:
                csrf = _seed_and_csrf(page, hotel, chunk[min(2, len(chunk) - 1)])
            if not csrf:
                log.warning("No CSRF for %s chunk starting %s", hotel["name"], chunk[0])
                price, prov, providers, csrf = _price_via_navigation(page, hotel, chunk[0])
                by_date[chunk[0].isoformat()] = DayPrice(
                    date=chunk[0].isoformat(),
                    lowest_price_inr=price,
                    lowest_provider=prov,
                    providers=providers,
                )
                i += 1
                time.sleep(1.0)
                continue

            burned = False
            for cin in chunk:
                day, new_csrf = _fetch_night(page, hotel, cin, csrf, adults=adults)
                if new_csrf is None and day.lowest_price_inr is None:
                    key = cin.isoformat()
                    fail_counts[key] = fail_counts.get(key, 0) + 1
                    log.info(
                        "%s browser chunk burned at %s (attempt %d, %d/%d done)",
                        hotel["name"],
                        cin,
                        fail_counts[key],
                        len(by_date),
                        len(nights),
                    )
                    if fail_counts[key] >= 2:
                        # One nav fallback before giving up
                        price, prov, providers, _c = _price_via_navigation(page, hotel, cin)
                        by_date[key] = DayPrice(
                            date=key,
                            lowest_price_inr=price,
                            lowest_provider=prov,
                            providers=providers,
                        )
                        i += 1
                        if price is None:
                            log.warning("%s no price for %s", hotel["name"], cin)
                    burned = True
                    break
                csrf = new_csrf
                by_date[day.date] = day
                i += 1
                time.sleep(0.25)

        log.info("%s calendar progress %d/%d", hotel["name"], len(by_date), len(nights))
        time.sleep(2.0 if burned else 1.0)

    days = [
        by_date.get(n.isoformat()) or DayPrice(date=n.isoformat(), lowest_price_inr=None)
        for n in nights
    ]
    base = f"https://www.kayak.co.in/hotels/{hotel['slug']}-details"
    return HotelCalendar(
        hotel=hotel["name"],
        hid=hotel["hid"],
        months=months,
        days=days,
        details_base_url=base,
    )


def fetch_tracked_calendars(
    *,
    today: date | None = None,
    adults: int = 2,
    headless: bool = True,
    hotels: tuple[dict[str, str], ...] | None = None,
) -> list[HotelCalendar]:
    today = today or date.today()
    months = calendar_month_range(today)
    nights = nights_for_months(months, today=today)
    hotel_list = hotels or TRACKED_HOTELS
    log.info(
        "Fetching calendars for %d hotels × %d nights (%s)",
        len(hotel_list),
        len(nights),
        ", ".join(f"{y}-{m:02d}" for y, m in months),
    )
    results: list[HotelCalendar] = []
    for hotel in hotel_list:
        log.info("=== Calendar %s ===", hotel["name"])
        results.append(
            fetch_hotel_calendar(hotel, nights, adults=adults, headless=headless)
        )
        time.sleep(3.0)
    return results
