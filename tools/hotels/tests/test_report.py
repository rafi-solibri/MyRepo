from tools.hotels.report import offers_to_csv, sort_offers
from tools.hotels.requirements_spec import EMAIL_TO, REQUIRED_AREAS


def test_required_areas_complete():
    assert "Botanical Garden" in REQUIRED_AREAS
    assert "Ayyappa Society" in REQUIRED_AREAS
    assert "100 Feet Road" in REQUIRED_AREAS
    assert "Raghavendra Colony" in REQUIRED_AREAS
    assert len(REQUIRED_AREAS) == 7


def test_email_recipient():
    assert EMAIL_TO == "rafi.success@gmail.com"


def test_sort_date_then_price():
    offers = [
        {"date": "2026-08-16", "lowest_price_inr": 1000, "hotel": "B"},
        {"date": "2026-08-15", "lowest_price_inr": 3000, "hotel": "A"},
        {"date": "2026-08-15", "lowest_price_inr": 1000, "hotel": "C"},
    ]
    sorted_ = sort_offers(offers)
    assert [o["hotel"] for o in sorted_] == ["C", "A", "B"]


def test_csv_has_header_and_rows():
    offers = [
        {
            "date": "2026-08-15",
            "day": "Saturday",
            "hotel": "Test Hotel",
            "area": "Madhapur",
            "stars": 4.0,
            "lowest_price_inr": 2000,
            "lowest_provider": "Agoda.com",
            "providers": [{"provider": "Agoda.com", "price_inr": 2000}],
            "source": "kayak",
        }
    ]
    csv_text = offers_to_csv(offers)
    assert "Lowest Price (INR)" in csv_text
    assert "Test Hotel" in csv_text


if __name__ == "__main__":
    test_required_areas_complete()
    test_email_recipient()
    test_sort_date_then_price()
    test_csv_has_header_and_rows()
    print("ok")
