"""Unit tests for Google Hotels price parsing (₹ and $ → INR)."""

from __future__ import annotations

from tools.hotels.calendar_google import _cut_similar, _parse_ladder
from tools.hotels.providers.google_hotels import DEFAULT_USD_INR, _prices_from_text


def test_prices_from_text_inr():
    assert _prices_from_text("Hotel Foo\n₹1,653\non Agoda") == [1653]


def test_prices_from_text_usd_converts():
    prices = _prices_from_text("Hotel Foo\n$22\non Agoda")
    assert len(prices) == 1
    assert prices[0] == int(round(22 * DEFAULT_USD_INR))


def test_prices_reject_tiny_usd_fees():
    assert _prices_from_text("Taxes\n$7\n") == []
    assert _prices_from_text("Fees\n$12\n") == []


def test_parse_ladder_cuts_similar_hotels():
    text = (
        "Hotel Qualia Oak\n"
        "Agoda\n₹1,653\n"
        "Booking.com\n₹1,980\n"
        "Similar hotels\n"
        "Other Place\nAgoda\n₹900\n"
    )
    providers = _parse_ladder(text)
    assert providers.get("Agoda") == 1653
    assert providers.get("Booking.com") == 1980
    assert min(providers.values()) == 1653


def test_parse_ladder_ignores_bare_page_min():
    text = "Hotel Qualia Oak\n$12\n$7\nSomething"
    assert _parse_ladder(text) == {}


def test_cut_similar():
    assert "Similar" not in _cut_similar("A\n₹1000\nSimilar hotels\nB\n₹500")
