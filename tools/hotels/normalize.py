from __future__ import annotations

import re
from collections import defaultdict

from rapidfuzz import fuzz

from .models import HotelOffer, ProviderPrice

_AREA_PHRASES = re.compile(
    r"\b(botanical\s+garden|ayyappa\s+society|100\s+feet\s+road|"
    r"raghavendra\s+colony|madhapur|kondapur|gachibowli)\b",
    re.I,
)
_NOISE = re.compile(
    r"\b(hotel|the|a|an|hyderabad|hitec|hitech|city|botanical|ayyappa|raghavendra)\b",
    re.I,
)


def normalize_name(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^\w\s]", " ", s)
    s = _AREA_PHRASES.sub(" ", s)
    s = _NOISE.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def merge_offers(
    offers: list[HotelOffer],
    *,
    fuzzy_threshold: int = 88,
) -> list[HotelOffer]:
    """Merge same hotel across providers/sources; keep all provider prices."""
    # Group by (date, rough name)
    groups: list[list[HotelOffer]] = []
    for offer in offers:
        key = normalize_name(offer.hotel)
        placed = False
        for group in groups:
            if group[0].check_in != offer.check_in:
                continue
            # Prefer same area, but allow cross-area near-duplicates
            gkey = normalize_name(group[0].hotel)
            score = fuzz.token_set_ratio(key, gkey)
            if score >= fuzzy_threshold:
                group.append(offer)
                placed = True
                break
        if not placed:
            groups.append([offer])

    merged: list[HotelOffer] = []
    for group in groups:
        # Prefer the longest / most specific hotel name
        base = max(group, key=lambda o: (len(o.hotel), o.stars, -o.lowest_price_inr))
        provider_map: dict[str, ProviderPrice] = {}
        areas = set()
        for o in group:
            areas.add(o.area)
            for p in o.providers:
                k = p.provider.lower()
                if k not in provider_map or p.price_inr < provider_map[k].price_inr:
                    provider_map[k] = p
            # Also record source as provider if only one price
            if not o.providers:
                k = o.lowest_provider.lower()
                pp = ProviderPrice(provider=o.lowest_provider, price_inr=o.lowest_price_inr)
                if k not in provider_map or pp.price_inr < provider_map[k].price_inr:
                    provider_map[k] = pp

        providers = sorted(provider_map.values(), key=lambda p: p.price_inr)
        if not providers:
            continue
        lowest = providers[0]
        area = base.area
        if len(areas) > 1:
            area = ", ".join(sorted(areas))

        merged.append(
            HotelOffer(
                hotel=base.hotel,
                area=area,
                check_in=base.check_in,
                stars=max(o.stars for o in group),
                lowest_price_inr=lowest.price_inr,
                lowest_provider=lowest.provider,
                providers=providers,
                source="+".join(sorted({o.source for o in group})),
                rating=next((o.rating for o in group if o.rating is not None), None),
                review_count=next((o.review_count for o in group if o.review_count is not None), None),
                hotel_id=base.hotel_id,
                details_url=base.details_url,
                neighborhood=base.neighborhood,
            )
        )

    merged.sort(key=lambda o: (o.check_in.isoformat(), o.lowest_price_inr, o.hotel.lower()))
    return merged


def sanitize_google_contaminated_offers(offers: list[HotelOffer]) -> list[HotelOffer]:
    """Drop Google $12-style crumbs and UI-chip names from merged inventory."""
    from .providers.google_hotels import MIN_INR, _is_ui_chip

    out: list[HotelOffer] = []
    for o in offers:
        if _is_ui_chip(o.hotel):
            continue
        providers: list[ProviderPrice] = []
        for p in o.providers:
            pname = (p.provider or "").lower()
            is_google = pname == "google hotels" or pname.startswith("google/")
            if is_google and p.price_inr < MIN_INR:
                continue
            providers.append(p)
        if not providers:
            # Google-only offer whose prices were all crumbs
            if o.source == "google" or (o.lowest_provider or "").lower() in {
                "google hotels",
                "google/google hotels",
            }:
                continue
            if o.lowest_price_inr < MIN_INR and "google" in (o.source or "").lower():
                continue
            continue
        providers = sorted(providers, key=lambda p: p.price_inr)
        lowest = providers[0]
        out.append(
            HotelOffer(
                hotel=o.hotel,
                area=o.area,
                check_in=o.check_in,
                stars=o.stars,
                lowest_price_inr=lowest.price_inr,
                lowest_provider=lowest.provider,
                providers=providers,
                source=o.source,
                rating=o.rating,
                review_count=o.review_count,
                hotel_id=o.hotel_id,
                details_url=o.details_url,
                neighborhood=o.neighborhood,
            )
        )
    out.sort(key=lambda o: (o.check_in.isoformat(), o.lowest_price_inr, o.hotel.lower()))
    return out


def summarize_by_provider(offers: list[HotelOffer]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for o in offers:
        for p in o.providers:
            counts[p.provider] += 1
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))
