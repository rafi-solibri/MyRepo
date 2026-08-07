"""Canonical product requirements for the Hotel Price Tracker automation.

Every cron / agent run MUST satisfy these. Do not shrink scope for “smoke”
tests unless the user explicitly asks for a sample.
"""

from __future__ import annotations

from .fetch import DEFAULT_AREAS

# --- Search scope ---
REQUIRED_AREAS: tuple[str, ...] = DEFAULT_AREAS
MIN_STARS: float = 4.0
ADULTS: int = 2
# Remaining Sat/Sun of the current calendar month (India/local date).
WEEKEND_SCOPE: str = "remaining_sat_sun_current_month"

# Kayak poll already returns Booking.com / Agoda / Expedia / brand OTAs.
# Direct scrapers are optional extras and often blocked from cloud IPs.
AUTOMATION_PROVIDERS: tuple[str, ...] = ("kayak",)

# --- Delivery ---
EMAIL_TO: str = "rafi.success@gmail.com"
EMAIL_FROM: str = "Hotel Price Watch <onboarding@resend.dev>"
EMAIL_SUBJECT_PREFIX: str = "Hyderabad 4★+ weekend hotel prices"

# Output must be tabular, sorted by check-in date then ascending lowest price,
# with a CSV attachment of the full inventory (all matching hotel-nights).
REQUIRE_FULL_INVENTORY: bool = True
REQUIRE_CSV_ATTACHMENT: bool = True
REQUIRE_HTML_TABLE: bool = True
SORT_ORDER: str = "date_asc_then_price_asc"
