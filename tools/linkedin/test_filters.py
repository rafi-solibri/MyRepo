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
    skip_reason("Senior Software Engineer – Python", "Curvia AI", "") is not None,
    "Python-primary senior engineer title must skip",
)
assert_true(
    skip_reason("Python / .NET Senior Engineer", "Acme", "") is None,
    "Python mention with .NET later on title must allow",
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
assert_true(
    skip_reason("Director, Data Engineering & Platforms", "Acme", "") is not None,
    "Data Engineering director without .NET must skip",
)
assert_true(
    skip_reason("Data Engineering Lead", "Acme", "") is not None,
    "Data Engineering Lead without .NET must skip",
)
assert_true(
    skip_reason("Oracle Cloud SCM Consultant / Architect", "Acme", "") is not None,
    "Oracle Cloud SCM title must skip",
)
assert_true(
    skip_reason("Finance Functional – Solution Architect", "Acme", "") is not None,
    "Finance Functional solution architect must skip",
)
assert_true(
    skip_reason("Tech Lead – Data Platform Cloud Engineer", "Acme", "") is not None,
    "Data Platform tech lead without .NET must skip",
)
assert_true(
    skip_reason("Data Engineering Architect .NET", "Acme", "") is None,
    "Data Engineering + .NET on title must allow",
)

for title in [
    "Director, Senior Engineering (.Net FullStack + AI/ML)",
    "Software Architect",
    "Cloud Architect .NET",
    "Lead Software Engineer",
    "Technology Lead",
    "Application Architect",
    "Manager, Software Development & Engineering",
    "Dot net with Angular - Walk In - Hyderabad",
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
    not location_allowed("India · 10 minutes ago · 1 applicant", "On-site"),
    "bare India without Remote pills / remote_search must reject (view default)",
)
assert_true(
    location_allowed("India · 10 minutes ago · 1 applicant", "On-site", remote_search=True),
    "bare India on remote-search wave must allow (view must pass remote_search)",
)
assert_true(
    skip_reason("Senior Staff DFT Engineer", "Mulya Technologies", "") is not None,
    "DFT / hardware staff title must skip",
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

assert_true(
    skip_reason(
        "Azure Data Engineer (7+ years) | Chennai | Bengaluru | Hyderabad",
        "Strive4X Infotech Private Limited",
        "",
    )
    is not None,
    "Azure Data Engineer title without .NET must skip (view bait-and-switch)",
)

print("filters self-test OK")
