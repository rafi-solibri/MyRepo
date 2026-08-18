#!/usr/bin/env python3
"""Unit checks for LinkedIn title/JD skip logic (no browser)."""
from __future__ import annotations

from filters import TITLE_OK, location_allowed, skip_reason


def assert_true(cond, msg):
    if not cond:
        raise AssertionError(msg)


# S&P Global false-skip: JD mentions Data Engineer but title is .NET Director
assert_true(
    skip_reason(
        "Director, Senior Engineering (.Net FullStack + AI/ML)",
        "S&P Global",
        "We also hire Data Engineer peers and collaborate with Salesforce admins.",
    )
    is None,
    "S&P Global .NET Director must NOT skip on incidental Data Engineer JD text",
)

assert_true(
    skip_reason("Salesforce Architect", "Acme", "Hyderabad remote") is not None,
    "Salesforce title must skip",
)
assert_true(
    skip_reason("Quality Engineering Lead", "Acme", "") is not None,
    "QE title must skip",
)
assert_true(
    skip_reason("Principal Engineer (Python)", "DevRabbit", "") is not None,
    "Python principal title must skip",
)
assert_true(
    skip_reason(
        "Technical Lead",
        "Acme",
        "Java is mandatory. 10+ years building Spring Boot services.",
    )
    is not None,
    "Java mandatory JD must skip",
)
assert_true(
    skip_reason("AI Architect", "Wipro", "Azure and .NET in skills laundry list") is not None,
    "pure AI title without .NET on title must skip",
)
assert_true(
    skip_reason("Java Technical Lead", "Avensys", "") is not None,
    "Java primary title must skip",
)
assert_true(
    skip_reason("Lead System Architect", "Pegasystems", "") is not None,
    "Pegasystems company must skip",
)
assert_true(
    skip_reason(
        "Engineering Manager - Data Center Electrical Design - AI/Hyperscale",
        "Sunstripe",
        "",
    )
    is not None,
    "electrical design EM must skip",
)
assert_true(
    skip_reason("AI/ML Architect", "ToggleNow", "") is not None,
    "AI/ML Architect title must skip",
)
assert_true(
    skip_reason("Senior SoC Director", "Acme", "") is not None,
    "SoC / silicon hardware director must skip",
)

for title in [
    "Director, Senior Engineering (.Net FullStack + AI/ML)",
    "Software Architect",
    "Cloud Architect .NET",
    "Lead Software Engineer",
    "Technology Lead",
    "Application Architect",
]:
    assert_true(TITLE_OK.search(title), f"TITLE_OK should match: {title}")

# Location: primary line wins — chrome Hyd must not false-allow Bengaluru/Mumbai
assert_true(
    location_allowed("Hyderabad, Telangana, India · 2 days ago", "On-site"),
    "Hyderabad primary must allow",
)
assert_true(
    location_allowed("Bengaluru & Hyderabad · 1 day ago", "Hybrid"),
    "dual-city with Hyderabad must allow",
)
assert_true(
    not location_allowed(
        "Greater Bengaluru Area · 2 days ago · 42 applicants",
        "Remote Hyderabad profile chrome leak",
    ),
    "Bengaluru primary must reject even if workplace mentions Hyderabad",
)
assert_true(
    not location_allowed(
        "Mumbai, Maharashtra, India · 6 days ago",
        "Hyderabad, Telangana · Easy Apply",
    ),
    "Mumbai primary must reject despite Hyd in workplace scrape",
)
assert_true(
    not location_allowed("Panchgani, Maharashtra, India · 3 days ago", "Remote"),
    "Panchgani/Maharashtra must reject",
)
assert_true(
    location_allowed("India · 7 minutes ago · 0 applicants", "Remote", remote_search=True),
    "India + remote_search must allow",
)
assert_true(
    not location_allowed("", "Remote Hyderabad", remote_search=True),
    "empty primary location must reject",
)
assert_true(
    location_allowed(
        "India · 4 minutes ago",
        "Bengaluru people-you-can-reach chrome",
        remote_search=True,
    ),
    "India primary + remote_search must allow even if workplace has other cities",
)

from auto_login import should_skip_password_after_gsi

assert_true(
    should_skip_password_after_gsi(
        [{"step": "google_sso", "started": True}, {"step": "google_sso", "clicked": True}],
        "google_sso",
        6,
    ),
    "clicked GSI + checkpoint must skip password",
)
assert_true(
    not should_skip_password_after_gsi(
        [{"step": "google_sso", "clicked": False}],
        "google_sso",
        6,
    ),
    "GSI not clicked — password fallback still allowed",
)
assert_true(
    not should_skip_password_after_gsi(
        [{"step": "password", "email": "raf***"}],
        "password",
        6,
    ),
    "password-first checkpoint does not use this skip",
)

print("filters self-test OK")
