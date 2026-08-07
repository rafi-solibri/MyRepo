from .agoda import fetch_agoda
from .booking import fetch_booking
from .google_hotels import fetch_google_hotels
from .hotels_com import fetch_hotels_com
from .indian_otas import (
    fetch_cleartrip,
    fetch_easemytrip,
    fetch_goibibo,
    fetch_makemytrip,
    fetch_yatra,
)
from .kayak import fetch_kayak

# Ordered: aggregators first (richest cross-OTA data), then direct OTAs.
PROVIDERS = {
    "kayak": fetch_kayak,
    "google": fetch_google_hotels,
    "booking": fetch_booking,
    "agoda": fetch_agoda,
    "hotels_com": fetch_hotels_com,
    "makemytrip": fetch_makemytrip,
    "goibibo": fetch_goibibo,
    "cleartrip": fetch_cleartrip,
    "easemytrip": fetch_easemytrip,
    "yatra": fetch_yatra,
}

# Kayak is the reliable multi-OTA source from cloud IPs (Booking/Agoda/Expedia
# prices included). Direct Indian OTAs are attempted but often blocked.
DEFAULT_PROVIDERS = [
    "kayak",
    "google",
    "booking",
    "agoda",
    "hotels_com",
    "makemytrip",
    "goibibo",
    "cleartrip",
    "easemytrip",
    "yatra",
]

# Fast path for nightly automations
CORE_PROVIDERS = ["kayak", "google", "booking", "agoda"]

__all__ = ["PROVIDERS", "DEFAULT_PROVIDERS"]
