#!/usr/bin/env python3
"""Small unit tests for Hitech City filters."""

from tools.hitechcity.careers_apply import CAREERS_TITLE_SKIP, card_location_ok
from tools.hitechcity.filters import (
    company_name_match,
    location_or_campus_ok,
    skip_reason,
    title_matches_senior_stack,
)


def test_title_ok():
    assert title_matches_senior_stack("Solution Architect .NET")
    assert title_matches_senior_stack("Engineering Manager")
    assert skip_reason("Salesforce Developer") is not None
    assert skip_reason("QA Engineer") is not None
    assert CAREERS_TITLE_SKIP.search("Staff Project Analyst")
    assert CAREERS_TITLE_SKIP.search("Embedded Software - System Test Architect")


def test_campus_location():
    assert location_or_campus_ok("Madhapur, Hyderabad")
    assert location_or_campus_ok("Knowledge City, HITEC City")
    assert location_or_campus_ok("Remote, India", "WFH")
    assert not location_or_campus_ok("Bengaluru, Karnataka")
    # Regression: bare "hitec" must not match inside "Architect"
    assert not location_or_campus_ok("Solutions Architect", "", "Solutions Architect role summary")


def test_careers_card_location():
    # US workplace in title must skip even if page chrome later mentions India.
    assert not card_location_ok(
        "Solutions Architect Austin, TX +3 locations",
        "Careers India footer language picker",
    )
    assert not card_location_ok(
        "Principal Architect, Azure Management Solutions United States, Washington, Redmond"
    )
    assert not card_location_ok("Cloud Engineering Manager", "Boca Raton, FL")
    assert card_location_ok(
        "Senior Lead Engineer – AI Platform Architecture Hyderabad, Telangana, India"
    )
    assert card_location_ok("Solutions Architect", "Hyderabad, Telangana, India")


def test_company_match():
    assert company_name_match("Microsoft", "Microsoft India")
    assert company_name_match("JPMorgan Chase", "J.P. Morgan")
    assert company_name_match("Meta", "Facebook")
    assert not company_name_match("Microsoft", "Oracle")


if __name__ == "__main__":
    test_title_ok()
    test_campus_location()
    test_careers_card_location()
    test_company_match()
    print("ok")
