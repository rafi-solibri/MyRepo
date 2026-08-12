#!/usr/bin/env python3
"""Small unit tests for Hitech City filters."""

from tools.hitechcity.careers_apply import CAREERS_TITLE_SKIP, card_location_ok, url_loc_hint
from tools.hitechcity.filters import (
    company_name_match,
    location_or_campus_ok,
    skip_reason,
    title_matches_senior_stack,
)
from tools.hitechcity.linkedin_target_apply import LI_TITLE_SKIP


def test_title_ok():
    assert title_matches_senior_stack("Solution Architect .NET")
    assert title_matches_senior_stack("Engineering Manager")
    assert skip_reason("Salesforce Developer") is not None
    assert skip_reason("QA Engineer") is not None
    assert CAREERS_TITLE_SKIP.search("Staff Project Analyst")
    assert CAREERS_TITLE_SKIP.search("Embedded Software - System Test Architect")
    assert CAREERS_TITLE_SKIP.search("Product Manager, Principal")
    assert LI_TITLE_SKIP.search("Staff/Principal GPU/CPU Kernel Optimization Engineer")
    assert LI_TITLE_SKIP.search("Network Architect")
    assert not LI_TITLE_SKIP.search("Software Engineer, Principal - C#")
    assert not LI_TITLE_SKIP.search("Solution Architect")


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
    assert not card_location_ok(
        "ACSM Solution Architect Manager United Kingdom, Berkshire, Reading + 3 more"
    )
    assert card_location_ok(
        "Senior Lead Engineer – AI Platform Architecture Hyderabad, Telangana, India"
    )
    assert card_location_ok("Solutions Architect", "Hyderabad, Telangana, India")
    # Workday URL encodes workplace when card title omits city.
    modmed = "https://modmed.wd501.myworkdayjobs.com/en-US/ModMed12/job/Boca-Raton-FL/Cloud-Engineering-Manager_R4806"
    assert "boca" in url_loc_hint(modmed).lower()
    assert not card_location_ok("Cloud Engineering Manager", url_loc_hint(modmed))


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
