#!/usr/bin/env python3
"""Small unit tests for Hitech City filters."""

from tools.hitechcity.ats_fill import frame_url_is_captcha_challenge
from tools.hitechcity.careers_apply import (
    CAREERS_TITLE_SKIP,
    JOB_ID_HREF_RE,
    NAV_CHROME_RE,
    card_location_ok,
    url_loc_hint,
)
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


def test_oraclecloud_parent_card_location():
    # Oracle Cloud HCM parent-card text often bundles title + city (Bengaluru must skip).
    assert not card_location_ok(
        "System Architect BENGALURU, KARNATAKA, India and 2 more HOT JOB"
    )
    assert card_location_ok(
        "Senior Lead Architect - Solution Architect Hyderabad, Telangana, India TechnologyArchitecture"
    )
    # SmartRecruiters location-group annotation must keep Hyd and drop Brazil/Malaysia.
    assert card_location_ok(
        "Solution Architect (Microsoft .NET/Azure Cloud) Full-time · Hyderabad, India"
    )
    assert not card_location_ok("Solutions Architect Full-time · São Carlos, Brazil")
    assert not card_location_ok(
        "Senior Software & Platform Architect Full-time · Cyberjaya, Malaysia"
    )
    # Workday US path tokens (Intel /job/US-Oregon-Hillsboro/).
    intel = "https://intel.wd1.myworkdayjobs.com/en-US/External/job/US-Oregon-Hillsboro/Sr-Security-Architect_JR0282220?q=architect"
    assert "oregon" in url_loc_hint(intel).lower()
    assert not card_location_ok("Sr. Security Architect", url_loc_hint(intel))
    pan = "https://jobs.paloaltonetworks.com/en/job/hyderabad/senior-staff-software-engineer/47263/96768473904"
    assert "hyderabad" in url_loc_hint(pan).lower()
    assert card_location_ok("Senior Staff Software Engineer", url_loc_hint(pan))
    # Oracle/JPMC job links inherit listing ?location=Hyderabad — path has no city.
    oracle_beng = (
        "https://careers.oracle.com/en/sites/jobsearch/job/338870/"
        "?keyword=architect&location=Hyderabad%2C+Telangana%2C+India"
    )
    assert "hyderabad" not in url_loc_hint(oracle_beng).lower()
    assert not card_location_ok("System Architect BENGALURU, KARNATAKA, India and 2 more")
    jpmc = "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/210694242/?keyword=architect&location=Hyderabad"
    assert JOB_ID_HREF_RE.search(jpmc)
    assert not NAV_CHROME_RE.search("Senior Lead Architect - Solution Architect")
    assert NAV_CHROME_RE.search("Skip to main content")


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
    assert not card_location_ok(
        "Cloud Solution Architect - Entry Level Romania, Bucharest, Bucharest"
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


def test_captcha_frame_ignores_hidden_badge():
    assert not frame_url_is_captcha_challenge(
        "https://www.recaptcha.net/recaptcha/api2/anchor?k=6LfwboYU"
    )
    assert frame_url_is_captcha_challenge(
        "https://www.google.com/recaptcha/api2/bframe?k=6Le6HuQr"
    )
    assert frame_url_is_captcha_challenge("https://geo.captcha-delivery.com/captcha/?initialCid=x")
    assert frame_url_is_captcha_challenge("https://challenges.cloudflare.com/cdn-cgi/challenge-platform/")


def test_hyland_icims_url():
    import json
    from pathlib import Path

    data = json.loads(Path(__file__).with_name("companies.json").read_text())
    hyland = next(c for c in data["companies"] if c["name"] == "Hyland")
    assert any("icims.com" in u for u in hyland["careersUrls"])
    intel = next(c for c in data["companies"] if c["name"] == "Intel")
    assert any("myworkdayjobs.com" in u for u in intel["careersUrls"])


if __name__ == "__main__":
    test_title_ok()
    test_campus_location()
    test_oraclecloud_parent_card_location()
    test_careers_card_location()
    test_company_match()
    test_captcha_frame_ignores_hidden_badge()
    test_hyland_icims_url()
    print("ok")
