from datetime import date

from tools.hotels.models import HotelOffer, ProviderPrice
from tools.hotels.normalize import merge_offers, normalize_name


def test_normalize_name_strips_noise():
    assert "qualia oak" in normalize_name("The Hotel Qualia Oak Madhapur")


def test_merge_keeps_cheapest_per_provider():
    a = HotelOffer(
        hotel="Hotel Qualia Oak",
        area="Madhapur",
        check_in=date(2026, 8, 15),
        stars=4,
        lowest_price_inr=1976,
        lowest_provider="Agoda.com",
        providers=[
            ProviderPrice("Agoda.com", 1976),
            ProviderPrice("Booking.com", 2375),
        ],
        source="kayak",
    )
    b = HotelOffer(
        hotel="Qualia Oak Hotel",
        area="Madhapur",
        check_in=date(2026, 8, 15),
        stars=4,
        lowest_price_inr=2100,
        lowest_provider="Booking.com",
        providers=[ProviderPrice("Booking.com", 2100)],
        source="booking",
    )
    merged = merge_offers([a, b])
    assert len(merged) == 1
    assert merged[0].lowest_price_inr == 1976
    by = {p.provider: p.price_inr for p in merged[0].providers}
    assert by["Booking.com"] == 2100
    assert by["Agoda.com"] == 1976


if __name__ == "__main__":
    test_normalize_name_strips_noise()
    test_merge_keeps_cheapest_per_provider()
    print("ok")
