#!/usr/bin/env python3
"""Unit checks for LinkedIn title/JD skip logic (no browser)."""
from __future__ import annotations

from filters import TITLE_OK, parse_list_card_text, skip_reason


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

for title in [
    "Director, Senior Engineering (.Net FullStack + AI/ML)",
    "Software Architect",
    "Cloud Architect .NET",
    "Lead Software Engineer",
    "Technology Lead",
    "Application Architect",
]:
    assert_true(TITLE_OK.search(title), f"TITLE_OK should match: {title}")

role, company, loc = parse_list_card_text(
    "Technical Architect-AWS Architect\n"
    "Technical Architect-AWS Architect with verification\n"
    "Impetus\n"
    "Greater Hyderabad Area (On-site)\n"
    "Viewed\n"
    "Easy Apply"
)
assert_true(role == "Technical Architect-AWS Architect", f"card role: {role}")
assert_true(company == "Impetus", f"card company: {company}")
assert_true("Hyderabad" in loc, f"card loc: {loc}")
assert_true(skip_reason(role, company, "") is None, "Impetus AWS Architect must not title-skip")

role, company, loc = parse_list_card_text(
    "Senior Data Engineer\n"
    "Senior Data Engineer with verification\n"
    "Quest Global\n"
    "Hyderabad, Telangana, India (On-site)\n"
    "12 school alumni work here"
)
assert_true(role == "Senior Data Engineer", f"de role: {role}")
assert_true(company == "Quest Global", f"de company: {company}")
assert_true(skip_reason(role, company, "") is not None, "Data Engineer card must skip")

from pathlib import Path as _P

src = next(_P(__file__).resolve().parent.glob("*_easy_apply.py")).read_text(encoding="utf-8")
assert_true("li[data-occludable-job-id]" in src, "easy apply must prefer occludable job cards")
assert_true("DETAIL_PANE_SEL" in src, "easy apply must scope meta to the detail pane")
# The old page-wide first job-view link false-skipped every later card.
parse_fn = src.split("def parse_card_meta", 1)[-1].split("def _ids_from_report_obj", 1)[0]
assert_true(
    "a[href*='/jobs/view/']" not in parse_fn and 'a[href*="/jobs/view/"]' not in parse_fn,
    "parse_card_meta must not use page-wide /jobs/view/ links",
)

print("filters self-test OK")
