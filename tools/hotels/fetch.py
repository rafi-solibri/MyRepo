from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from typing import Iterable

from .browser import browser_session
from .models import HotelOffer, SearchQuery
from .normalize import merge_offers, summarize_by_provider
from .providers import DEFAULT_PROVIDERS, PROVIDERS

log = logging.getLogger(__name__)

DEFAULT_AREAS = ("Madhapur", "Kondapur", "Gachibowli")


def weekend_dates(year: int, month: int, *, include_past: bool = False, today: date | None = None) -> list[date]:
    """Return every Saturday and Sunday in the given month."""
    today = today or date.today()
    days: list[date] = []
    d = date(year, month, 1)
    while d.month == month:
        if d.weekday() in (5, 6):  # Sat, Sun
            if include_past or d >= today:
                days.append(d)
        d += timedelta(days=1)
    return days


def fetch_prices(
    *,
    areas: Iterable[str] = DEFAULT_AREAS,
    dates: Iterable[date] | None = None,
    providers: Iterable[str] | None = None,
    min_stars: float = 4.0,
    adults: int = 2,
    merge: bool = True,
    headless: bool = True,
) -> list[HotelOffer]:
    """Fetch hotel offers across areas/dates/providers and optionally merge."""
    provider_names = list(providers or DEFAULT_PROVIDERS)
    unknown = [p for p in provider_names if p not in PROVIDERS]
    if unknown:
        raise ValueError(f"Unknown providers: {unknown}. Known: {sorted(PROVIDERS)}")

    date_list = list(dates or [])
    if not date_list:
        today = date.today()
        date_list = weekend_dates(today.year, today.month, include_past=False, today=today)

    queries = [
        SearchQuery(
            area=area,
            check_in=d,
            check_out=d + timedelta(days=1),
            adults=adults,
            min_stars=min_stars,
        )
        for area in areas
        for d in date_list
    ]

    all_offers: list[HotelOffer] = []
    # One shared browser context; providers run sequentially per query to avoid
    # hammering sites, but queries can be parallelized lightly.
    with browser_session(headless=headless) as (_p, _browser, context):
        for query in queries:
            log.info("=== %s %s ===", query.area, query.check_in)
            for name in provider_names:
                fn = PROVIDERS[name]
                try:
                    offers = fn(context, query)
                except Exception:
                    log.exception("Provider %s failed for %s %s", name, query.area, query.check_in)
                    offers = []
                all_offers.extend(offers)

    if merge:
        merged = merge_offers(all_offers)
        log.info(
            "Merged %d raw offers -> %d hotels | providers seen: %s",
            len(all_offers),
            len(merged),
            summarize_by_provider(merged),
        )
        return merged
    return all_offers


def fetch_prices_parallel_providers(
    query: SearchQuery,
    provider_names: list[str],
    *,
    headless: bool = True,
    max_workers: int = 3,
) -> list[HotelOffer]:
    """Fetch one query from multiple providers using separate browser contexts."""

    def _run(name: str) -> list[HotelOffer]:
        with browser_session(headless=headless) as (_p, _b, context):
            return PROVIDERS[name](context, query)

    results: list[HotelOffer] = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futs = {pool.submit(_run, n): n for n in provider_names}
        for fut in as_completed(futs):
            name = futs[fut]
            try:
                results.extend(fut.result())
            except Exception:
                log.exception("Parallel provider %s failed", name)
    return results
