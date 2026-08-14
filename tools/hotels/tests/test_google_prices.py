"""Unit tests for Google Hotels price parsing (₹ and $ → INR)."""

from __future__ import annotations

from datetime import date

from tools.hotels.calendar_google import (
    _cut_similar,
    _parse_ladder,
    merge_google_day,
    strip_untrusted_google_from_calendar,
)
from tools.hotels.calendar_prices import DayPrice, HotelCalendar
from tools.hotels.models import HotelOffer, ProviderPrice
from tools.hotels.normalize import sanitize_google_contaminated_offers
from tools.hotels.providers.google_hotels import (
    DEFAULT_USD_INR,
    _is_ui_chip,
    _prices_from_text,
)


def test_prices_from_text_inr():
    assert _prices_from_text("Hotel Foo\n₹1,653\non Agoda") == [1653]


def test_prices_from_text_usd_converts():
    prices = _prices_from_text("Hotel Foo\n$19\non Agoda")
    assert len(prices) == 1
    assert prices[0] == int(round(19 * DEFAULT_USD_INR))


def test_prices_reject_tiny_usd_fees():
    assert _prices_from_text("Taxes\n$7\n") == []


def test_prices_reject_twelve_dollar_great_price_chip():
    assert _prices_from_text("GREAT PRICE\n$12\n$12 nightly\n$13 total") == []
    assert _prices_from_text("Hotel Foo\n$12\n") == []


def test_ui_chip_rejects_great_price_blob():
    assert _is_ui_chip("GREAT PRICE$12$12 nightly$13 total1 night with taxes + fees$")
    assert not _is_ui_chip("Hotel Qualia Oak")


def test_parse_ladder_cuts_similar_hotels():
    text = (
        "Hotel Qualia Oak\n"
        "Agoda\n₹1,653\n"
        "Booking.com\n₹1,980\n"
        "Similar hotels\n"
        "Other Place\n₹900\n"
    )
    providers = _parse_ladder(text)
    assert providers.get("Agoda") == 1653
    assert "Other Place" not in str(providers)
    assert min(providers.values()) == 1653


def test_parse_ladder_ignores_usd12_page_min():
    text = "Hotel Qualia Oak\nGREAT PRICE\n$12 nightly\n$13 total\n"
    assert _parse_ladder(text) == {}


def test_cut_similar():
    assert "Similar" not in _cut_similar("A\n₹1000\nSimilar hotels\nB\n₹500")


def test_merge_google_day_does_not_let_bare_page_min_undercut_kayak():
    kayak = DayPrice(
        date="2026-08-15",
        lowest_price_inr=1979,
        lowest_provider="Agoda.com",
        providers={"Agoda.com": 1979, "Booking.com": 2374},
    )
    google = DayPrice(
        date="2026-08-15",
        lowest_price_inr=1044,
        lowest_provider="Google/Google Hotels",
        providers={"Google/Google Hotels": 1044},
    )
    merged = merge_google_day(kayak, google)
    assert merged.lowest_price_inr == 1979
    assert merged.lowest_provider == "Agoda.com"
    assert "Google/Google Hotels" not in merged.providers


def test_merge_google_day_named_ota_can_win():
    kayak = DayPrice(
        date="2026-08-15",
        lowest_price_inr=1979,
        lowest_provider="Agoda.com",
        providers={"Agoda.com": 1979},
    )
    google = DayPrice(
        date="2026-08-15",
        lowest_price_inr=1653,
        lowest_provider="Google/Agoda",
        providers={"Google/Agoda": 1653},
    )
    merged = merge_google_day(kayak, google)
    assert merged.lowest_price_inr == 1653
    assert merged.lowest_provider == "Google/Agoda"


def test_strip_untrusted_google_from_calendar():
    cal = HotelCalendar(
        hotel="Hotel Qualia Oak",
        hid="1",
        months=["2026-08"],
        days=[
            DayPrice(
                "2026-08-15",
                1044,
                "Google/Google Hotels",
                {"Agoda.com": 1979, "Google/Google Hotels": 1044},
            )
        ],
        details_base_url="https://example.com",
    )
    out = strip_untrusted_google_from_calendar(cal)
    assert out.days[0].lowest_price_inr == 1979
    assert out.days[0].lowest_provider == "Agoda.com"


def test_sanitize_drops_google_crumb_offers():
    junk = HotelOffer(
        hotel="GREAT PRICE$12$12 nightly$13 total1 night with taxes + fees$",
        area="Ayyappa Society",
        check_in=date(2026, 8, 15),
        stars=4.0,
        lowest_price_inr=1044,
        lowest_provider="Google Hotels",
        providers=[ProviderPrice(provider="Google Hotels", price_inr=1044)],
        source="google",
    )
    mixed = HotelOffer(
        hotel="Super Collection O Rio",
        area="Kondapur",
        check_in=date(2026, 8, 15),
        stars=4.0,
        lowest_price_inr=1044,
        lowest_provider="Google Hotels",
        providers=[
            ProviderPrice(provider="Google Hotels", price_inr=1044),
            ProviderPrice(provider="Agoda.com", price_inr=1979),
        ],
        source="google+kayak",
    )
    out = sanitize_google_contaminated_offers([junk, mixed])
    assert [o.hotel for o in out] == ["Super Collection O Rio"]
    assert out[0].lowest_price_inr == 1979
    assert out[0].lowest_provider == "Agoda.com"


if __name__ == "__main__":
    test_prices_from_text_inr()
    test_prices_from_text_usd_converts()
    test_prices_reject_tiny_usd_fees()
    test_prices_reject_twelve_dollar_great_price_chip()
    test_ui_chip_rejects_great_price_blob()
    test_parse_ladder_cuts_similar_hotels()
    test_parse_ladder_ignores_usd12_page_min()
    test_cut_similar()
    test_merge_google_day_does_not_let_bare_page_min_undercut_kayak()
    test_merge_google_day_named_ota_can_win()
    test_strip_untrusted_google_from_calendar()
    test_sanitize_drops_google_crumb_offers()
    print("ok")
