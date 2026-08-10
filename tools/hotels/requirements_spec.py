"""Canonical product requirements for the Hotel Price Tracker automation.

Every cron / agent run MUST satisfy these. Do not shrink scope for “smoke”
tests unless the user explicitly asks for a sample.
"""

from __future__ import annotations

from .calendar_prices import TRACKED_HOTELS
from .fetch import DEFAULT_AREAS

# --- Search scope ---
REQUIRED_AREAS: tuple[str, ...] = DEFAULT_AREAS
MIN_STARS: float = 4.0
ADULTS: int = 2
# Remaining Sat/Sun of the current calendar month (India/local date).
WEEKEND_SCOPE: str = "remaining_sat_sun_current_month"

# Kayak poll returns Booking.com / Agoda / Expedia / brand OTAs; Google Hotels
# is a second aggregator surface (often shows $ from cloud — converted to INR).
AUTOMATION_PROVIDERS: tuple[str, ...] = ("kayak", "google")
REQUIRE_GOOGLE_HOTELS_EVERYWHERE: bool = True
REQUIRE_GOOGLE_HOTELS_IN_CALENDARS: bool = True
REQUIRE_GOOGLE_HOTELS_IN_INVENTORY: bool = True

# --- MOST IMPORTANT: per-hotel calendars (current + next month) ---
# Lowest nightly price across all compared hotel providers for each day.
REQUIRE_HOTEL_CALENDARS: bool = True
CALENDAR_HOTELS: tuple[dict[str, str], ...] = TRACKED_HOTELS
CALENDAR_MONTHS: str = "current_and_next"

# --- Delivery ---
EMAIL_TO: str = "rafi.success@gmail.com"
EMAIL_FROM: str = "Hotel Price Watch <onboarding@resend.dev>"
EMAIL_SUBJECT_PREFIX: str = "Hyderabad hotel prices + Qualia/Oak calendars"

# Output must be tabular, sorted by check-in date then ascending lowest price,
# with a CSV attachment of the full inventory (all matching hotel-nights).
# Email HTML MUST lead with the Qualia Oak + Oak Business calendar views.
REQUIRE_FULL_INVENTORY: bool = True
REQUIRE_CSV_ATTACHMENT: bool = True
REQUIRE_HTML_TABLE: bool = True
SORT_ORDER: str = "date_asc_then_price_asc"
