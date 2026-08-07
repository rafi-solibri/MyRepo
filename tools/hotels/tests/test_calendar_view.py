from datetime import date

from tools.hotels.calendar_prices import DayPrice, HotelCalendar
from tools.hotels.calendar_view import render_hotel_calendar_html
from tools.hotels.requirements_spec import CALENDAR_HOTELS, REQUIRE_HOTEL_CALENDARS


def test_calendar_hotels_required():
    assert REQUIRE_HOTEL_CALENDARS is True
    names = {h["name"] for h in CALENDAR_HOTELS}
    assert "Hotel Qualia Oak" in names
    assert "Oak Business Hotel" in names


def test_render_includes_prices_and_months():
    cal = HotelCalendar(
        hotel="Hotel Qualia Oak",
        hid="1",
        months=["2026-08", "2026-09"],
        days=[
            DayPrice("2026-08-08", 1715, "Agoda.com", {"Agoda.com": 1715, "Booking.com": 2000}),
            DayPrice("2026-09-04", 1412, "Agoda.com", {"Agoda.com": 1412}),
        ],
        details_base_url="https://example.com",
    )
    html = render_hotel_calendar_html(cal, today=date(2026, 8, 7))
    assert "Hotel Qualia Oak" in html
    assert "August" in html and "September" in html
    assert "₹1,715" in html
    assert "₹1,412" in html


if __name__ == "__main__":
    test_calendar_hotels_required()
    test_render_includes_prices_and_months()
    print("ok")
