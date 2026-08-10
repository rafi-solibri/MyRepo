#!/usr/bin/env python3
"""Unit checks for LinkedIn title/JD skip logic (no browser)."""
from __future__ import annotations

from filters import TITLE_OK, skip_reason


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

for title in [
    "Director, Senior Engineering (.Net FullStack + AI/ML)",
    "Software Architect",
    "Cloud Architect .NET",
    "Lead Software Engineer",
    "Technology Lead",
    "Application Architect",
]:
    assert_true(TITLE_OK.search(title), f"TITLE_OK should match: {title}")

print("filters self-test OK")
