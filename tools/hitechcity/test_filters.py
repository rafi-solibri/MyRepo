#!/usr/bin/env python3
"""Small unit tests for Hitech City filters."""

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


def test_campus_location():
    assert location_or_campus_ok("Madhapur, Hyderabad")
    assert location_or_campus_ok("Knowledge City, HITEC City")
    assert location_or_campus_ok("Remote, India", "WFH")
    assert not location_or_campus_ok("Bengaluru, Karnataka")
    # Regression: bare "hitec" must not match inside "Architect"
    assert not location_or_campus_ok("Solutions Architect", "", "Solutions Architect role summary")


def test_company_match():
    assert company_name_match("Microsoft", "Microsoft India")
    assert company_name_match("JPMorgan Chase", "J.P. Morgan")
    assert company_name_match("Meta", "Facebook")
    assert not company_name_match("Microsoft", "Oracle")


if __name__ == "__main__":
    test_title_ok()
    test_campus_location()
    test_company_match()
    print("ok")
