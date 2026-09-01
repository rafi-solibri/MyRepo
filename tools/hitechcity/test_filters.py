#!/usr/bin/env python3
"""Small unit tests for Hitech City filters."""

import json
import re

from tools.hitechcity.ats_fill import (
    attempt_ats_apply,
    auth_wall_url,
    blocked_wall,
    frame_url_is_captcha_challenge,
)
from tools.hitechcity.careers_apply import (
    CAREERS_TITLE_SKIP,
    JD_WRONG_STACK,
    JOB_ID_HREF_RE,
    NAV_CHROME_RE,
    _browser_session_dead,
    card_location_ok,
    company_skip_reason,
    is_hang_scan_url,
    is_sso_only_careers_url,
    is_uhg_skip_url,
    location_ui_input_meta_ok,
    role_has_foreign_location,
    url_loc_hint,
)
from tools.hitechcity.filters import (
    company_name_match,
    location_or_campus_ok,
    skip_reason,
    title_matches_senior_stack,
)
from tools.hitechcity.linkedin_target_apply import LI_TITLE_SKIP


def test_browser_session_dead():
    assert _browser_session_dead("Page.goto: Target page, context or browser has been closed")
    assert _browser_session_dead("connect ECONNREFUSED 127.0.0.1:9222")
    assert not _browser_session_dead("Timeout 75000ms exceeded")


def test_title_ok():
    assert title_matches_senior_stack("Solution Architect .NET")
    assert title_matches_senior_stack("Engineering Manager")
    assert title_matches_senior_stack("Manager of Software Engineering")
    assert title_matches_senior_stack("Director of Engineering")
    assert title_matches_senior_stack("Staff Software Engineer")
    assert title_matches_senior_stack("Lead Software Engineer")
    assert title_matches_senior_stack("Software Development Manager")
    assert title_matches_senior_stack("Principal Software Engineer")
    assert title_matches_senior_stack("Senior Software Engineer - .NET")
    assert title_matches_senior_stack("Sr. Software Engineer")
    assert not title_matches_senior_stack("Software Engineer II")
    assert not title_matches_senior_stack("Software Engineer")
    # Owner: never apply to AI/ML titles.
    assert not title_matches_senior_stack(
        "Staff/Principal Engineer - AI/ML & System-Level Validation"
    )
    assert skip_reason("Staff/Principal Engineer - AI/ML & System-Level Validation") == "title: AI/ML excluded"
    assert skip_reason("Machine Learning Engineer") == "title: AI/ML excluded"
    assert skip_reason("GenAI Architect") == "title: AI/ML excluded"
    assert CAREERS_TITLE_SKIP.search("Staff/Principal Engineer - AI/ML & System-Level Validation")
    assert LI_TITLE_SKIP.search("Staff/Principal Engineer - AI/ML & System-Level Validation")
    assert skip_reason("Salesforce Developer") is not None
    assert skip_reason("QA Engineer") is not None
    assert CAREERS_TITLE_SKIP.search("Staff Project Analyst")
    assert CAREERS_TITLE_SKIP.search("Principal Project Manager India, Telangana, Hyderabad")
    assert CAREERS_TITLE_SKIP.search("Principal Software Development Engineer in Test")
    assert CAREERS_TITLE_SKIP.search(
        "Principal Performance Test Engineer (Fusion Load Testing) HYDERABAD"
    )
    assert CAREERS_TITLE_SKIP.search("CyberSecurity Architect - CNI")
    assert CAREERS_TITLE_SKIP.search("Principal Database Engineer- Architecture/Engineering")
    assert CAREERS_TITLE_SKIP.search("Embedded Software - System Test Architect")
    assert CAREERS_TITLE_SKIP.search("Product Manager, Principal")
    assert CAREERS_TITLE_SKIP.search("Principal Physical Design Engineer (Chiplet Design)")
    assert CAREERS_TITLE_SKIP.search("Staff ASIC Design Engineer")
    assert CAREERS_TITLE_SKIP.search("Principal Silicon Design Engineer")
    assert CAREERS_TITLE_SKIP.search("Principal Silicon Design Engineer India, Telangana, Hyderabad")
    assert CAREERS_TITLE_SKIP.search("Product Design Manager")
    assert CAREERS_TITLE_SKIP.search(
        "Lead Principal Technical Program Manager DUBAI, United Arab Emirates"
    )
    assert CAREERS_TITLE_SKIP.search("Technical Program Manager")
    # Micron HW inventory that matched Staff/Principal via TITLE_OK (#294).
    assert CAREERS_TITLE_SKIP.search(
        "Staff Engineer, Scribe Layout Design Hyderabad, Telangana, India"
    )
    assert CAREERS_TITLE_SKIP.search(
        "Member Of Technical Staff TLP - HBM Verification Hyderabad, Telangana, India"
    )
    assert CAREERS_TITLE_SKIP.search(
        "Lead Principal Engineer, Design Verification Hyderabad, Telangana, India"
    )
    assert CAREERS_TITLE_SKIP.search(
        "Design Methodology – Senior / Staff DRAM Power Integrity Engineer Hyderabad"
    )
    assert CAREERS_TITLE_SKIP.search("Staff Engineer - Standard Cell Design Hyderabad")
    assert CAREERS_TITLE_SKIP.search(
        "STAFF ENGINEER, SSD NVMQRA TEST DEV ENG Hyderabad, Telangana, India"
    )
    assert CAREERS_TITLE_SKIP.search("Staff Data Science Engineer, SMAI Hyderabad")
    # Micron HW / ops titles that still matched Staff/Principal via TITLE_OK (2026-09-01).
    assert CAREERS_TITLE_SKIP.search("Staff Engineer, CAD Hyderabad, Telangana, India")
    assert CAREERS_TITLE_SKIP.search(
        "Principal Engineer - STA/Synthesis Hyderabad, Telangana, India"
    )
    assert CAREERS_TITLE_SKIP.search(
        "Staff Analyst - IT EA EPS Hyderabad, Telangana, India"
    )
    assert LI_TITLE_SKIP.search("Staff Engineer, CAD")
    assert LI_TITLE_SKIP.search("Principal Engineer - STA/Synthesis")
    assert LI_TITLE_SKIP.search("Staff Analyst - IT EA EPS")
    assert LI_TITLE_SKIP.search("Staff Engineer, Scribe Layout Design")
    assert LI_TITLE_SKIP.search("Lead Principal Engineer, Design Verification")
    assert skip_reason("Staff Engineer, Scribe Layout Design") is not None
    assert LI_TITLE_SKIP.search("Principal Silicon Design Engineer")
    assert JD_WRONG_STACK.search("We need a Mobile Architect for Ionic Capacitor and Zscaler")
    assert JD_WRONG_STACK.search(
        "designing and implementing Salesforce solutions ... SFDC Development and Customization"
    )
    assert LI_TITLE_SKIP.search("Staff/Principal GPU/CPU Kernel Optimization Engineer")
    assert LI_TITLE_SKIP.search("Network Architect")
    assert LI_TITLE_SKIP.search("Principal Physical Design Engineer")
    assert not LI_TITLE_SKIP.search("Software Engineer, Principal - C#")
    assert not LI_TITLE_SKIP.search("Solution Architect")
    assert not CAREERS_TITLE_SKIP.search("Principal Software Engineer")
    assert not CAREERS_TITLE_SKIP.search("Solution Architect (Microsoft .NET/Azure Cloud)")
    assert not CAREERS_TITLE_SKIP.search("Staff Software Engineer - .NET")
    assert not CAREERS_TITLE_SKIP.search("Staff ENGINEER, Software Development, SMAI Hyderabad")
    # LinkedIn company-jobs keywords must not be architect-only / architect-first.
    from tools.hitechcity.linkedin_target_apply import SEARCH_KEYWORDS

    assert SEARCH_KEYWORDS[0] == "Engineering Manager"
    assert any("Staff" in k for k in SEARCH_KEYWORDS)
    assert any("Lead" in k for k in SEARCH_KEYWORDS)
    assert any("Manager" in k for k in SEARCH_KEYWORDS)
    assert SEARCH_KEYWORDS.index("Engineering Manager") < SEARCH_KEYWORDS.index("Solution Architect")
    from tools.hitechcity.linkedin_target_apply import company_jobs_url

    url_fc = company_jobs_url("jpmorganchase", "Engineering Manager", company_f_c="1068")
    assert "jobs/search" in url_fc and "f_C=1068" in url_fc
    assert "Hyderabad" in url_fc and "geoId=105556991" in url_fc and "distance=25" in url_fc
    url_fb = company_jobs_url("jpmorganchase", "Engineering Manager")
    assert "/company/jpmorganchase/jobs/" in url_fb and "geoId=105556991" in url_fb
    # Careers portals: multi-role + Hyderabad location on every scan URL.
    from tools.hitechcity.careers_apply import (
        CAREERS_SEARCH_KEYWORDS,
        expand_careers_scan_urls,
        pin_careers_hyderabad_location,
        rewrite_careers_search_keyword,
    )

    assert CAREERS_SEARCH_KEYWORDS[0] == "Engineering Manager"
    assert CAREERS_SEARCH_KEYWORDS.index("Engineering Manager") < CAREERS_SEARCH_KEYWORDS.index(
        "Solution Architect"
    )
    by = "https://careers.blueyonder.com/us/en/search-results?keywords=architect&location=Bengaluru"
    assert "Engineering%20Manager" in rewrite_careers_search_keyword(by, "Engineering Manager") or (
        "Engineering+Manager" in rewrite_careers_search_keyword(by, "Engineering Manager")
    )
    pinned = pin_careers_hyderabad_location(by)
    assert "Hyderabad" in pinned and "Bengaluru" not in pinned
    expanded = expand_careers_scan_urls([by])
    assert len(expanded) >= 4
    assert any("Engineering" in u for u in expanded)
    assert all("Hyderabad" in u for u in expanded)
    # Workday: always invent/keep location=Hyderabad on the URL; UI facet is separate.
    intel = (
        "https://intel.wd1.myworkdayjobs.com/en-US/External"
        "?q=Engineering+Manager"
    )
    pinned_intel = pin_careers_hyderabad_location(intel)
    assert "location=Hyderabad" in pinned_intel or "location=Hyderabad".lower() in pinned_intel.lower()
    # Portals with NO location param must still get Hyderabad invented.
    ge = pin_careers_hyderabad_location(
        "https://careers.gevernova.com/global/en/search-results?keywords=Engineering+Manager"
    )
    assert "location=Hyderabad" in ge
    hyland = pin_careers_hyderabad_location(
        "https://careers-hyland.icims.com/jobs/search?ss=1&searchKeyword=Engineering+Manager&in_iframe=1"
    )
    assert "Hyderabad" in hyland
    assert not card_location_ok(
        "Security Researcher Technical Lead · Israel, Haifa",
        url_loc_hint(
            "https://intel.wd1.myworkdayjobs.com/en-US/External/job/Israel-Haifa/"
            "Security-Researcher-Technical-Lead_JR0286006"
        ),
    )
    assert role_has_foreign_location("Security Researcher Technical Lead · Israel, Haifa")
    assert not card_location_ok(
        "CPU DFT Manager · India, Bangalore",
        "India Bangalore",
    )
    # Discovery must not use campus-name LinkedIn queries.
    from tools.hitechcity import discover_tenants as disc

    assert not hasattr(disc, "LI_SEARCHES") or not any(
        re.search(r"knowledge city|raheja mindspace", q, re.I) for q in getattr(disc, "LI_SEARCHES", [])
    )
    assert any("HighRadius" in q for q in disc.LI_COMPANY_NAME_QUERIES)
    assert not any(re.search(r"knowledge city|raheja", q, re.I) for q in disc.LI_COMPANY_NAME_QUERIES)


def test_short_company_name_match_no_false_substring():
    assert company_name_match("EY", "EY")
    assert not company_name_match("EY", "Blue Yonder")
    assert not company_name_match("Blue Yonder", "EY")
    assert company_name_match("CGI", "CGI")
    assert not company_name_match("CGI", "Cognizant")
    assert company_name_match("GE Vernova", "GE Vernova")
    assert company_name_match("Meta", "Facebook")  # alias still works (len>3 path via aliases… Meta is 4)


def test_campus_location():
    assert location_or_campus_ok("Madhapur, Hyderabad")
    assert location_or_campus_ok("Knowledge City, HITEC City")
    assert location_or_campus_ok("RMZ Nexity, HITEC City")
    assert location_or_campus_ok("The Skyview Madhapur")
    assert location_or_campus_ok("Raheja Mindspace")
    assert location_or_campus_ok("Remote, India", "WFH")
    assert not location_or_campus_ok("Bengaluru, Karnataka")
    assert not location_or_campus_ok("Remote, Canada")
    assert not location_or_campus_ok("Remote - United States")
    # Regression: bare "hitec" must not match inside "Architect"
    assert not location_or_campus_ok("Solutions Architect", "", "Solutions Architect role summary")


def test_oraclecloud_parent_card_location():
    # Oracle Cloud HCM parent-card text often bundles title + city (Bengaluru must skip).
    assert not card_location_ok(
        "System Architect BENGALURU, KARNATAKA, India and 2 more HOT JOB"
    )
    # Regression: Dubai/UAE must never open — even with Hyd search URL / "and 1 more".
    assert not card_location_ok(
        "Lead Principal Technical Program Manager DUBAI, United Arab Emirates and 1 more"
    )
    assert role_has_foreign_location(
        "Lead Principal Technical Program Manager DUBAI, United Arab Emirates and 1 more"
    )
    # Multi-location naming Dubai + Hyderabad is still not Hyd-only.
    assert not card_location_ok(
        "Technical Program Manager Hyderabad, Telangana, India and Dubai, UAE"
    )
    assert card_location_ok(
        "Senior Lead Architect - Solution Architect Hyderabad, Telangana, India TechnologyArchitecture"
    )
    # Hyd-only title must not false-skip when ATS chrome lists other offices.
    assert card_location_ok(
        "Senior Principal Forward Deployed Engineer HYDERABAD",
        "Bengaluru Dubai United States office directory",
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
    # Remote Canada / Remote US / Remote UK are not India-remote (Gartner Workday path).
    assert not card_location_ok(
        "Sr. Director Analyst, Enterprise Architecture (Remote)",
        "Remote, Nova Scotia, Canada",
    )
    gartner_ca = (
        "https://gartner.wd5.myworkdayjobs.com/en-US/EXT/job/Remote---Nova-Scotia/"
        "Sr-Director-Analyst--Enterprise-Architecture--Remote-Canada-_106975/apply/applyManually"
    )
    assert "nova scotia" in url_loc_hint(gartner_ca).lower()
    assert not card_location_ok(
        "Sr. Director Analyst, Enterprise Architecture (Remote)",
        url_loc_hint(gartner_ca),
    )
    assert not card_location_ok(
        "Sr. Director Analyst, Enterprise Architecture (Remote US)",
        "Remote - United States",
    )
    # Gartner title punctuation: Remote- US / Remote - U.S. / Remote - N.A.
    assert not card_location_ok(
        "Sr Director Analyst, AI and Software Engineering (Remote- US)"
    )
    assert not card_location_ok(
        "Senior Director Analyst - Software Engineering for AI and Agentic Applications "
        "(Remote - U.S.)"
    )
    assert not card_location_ok(
        "Sr Director Analyst - Software Engineering AI Strategy and Value (Remote - N.A.)"
    )
    assert not card_location_ok(
        "Sr Director Analyst - Software Engineering AI Strategy and Value (Remote-N.A.)"
    )
    assert not card_location_ok(
        "Sr Director Analyst, Software Engineering (Remote - North America)"
    )
    gartner_tx = (
        "https://gartner.wd5.myworkdayjobs.com/en-US/EXT/job/Remote---Texas/"
        "Sr-Director-Analyst--AI-and-Software-Engineering--Remote--US-_104591-1/"
        "apply/applyManually"
    )
    assert not card_location_ok(
        "Sr Director Analyst, AI and Software Engineering (Remote- US)",
        url_loc_hint(gartner_tx),
    )
    assert card_location_ok("Solution Architect", "Fully Remote")
    assert card_location_ok("Solution Architect", "Remote, India")
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


class _FakeLoc:
    def __init__(self, n=0):
        self._n = n

    def count(self):
        return self._n


class _FakePage:
    """Minimal page stub for blocked_wall unit checks."""

    def __init__(self, body: str, *, file_inputs: int = 0, create_acct: bool = False):
        self._body = body
        self._file = file_inputs
        self._create = create_acct
        self.frames = []
        self.url = "https://solera.wd5.myworkdayjobs.com/apply/applyManually"

    def locator(self, sel: str):
        s = (sel or "").lower()
        if "input[type='file']" in s or 'input[type="file"]' in s:
            return _FakeLoc(self._file)
        if "createaccountsubmitbutton" in s:
            return _FakeLoc(1 if self._create else 0)
        if "password" in s:
            return _FakeLoc(1 if self._create else 0)
        if sel == "body" or s == "body":
            page = self

            class _Body:
                def inner_text(self, *a, **k):
                    return page._body

            return _Body()
        return _FakeLoc(0)


def test_workday_create_account_is_completable():
    body = (
        "Create Account/Sign In\nMy Information\nCreate Account\n"
        "Password Requirements:\nEmail Address*\nPassword*\nVerify New Password*\n"
        "Already have an account?\nSign In"
    )
    # Workday step 1 has no resume input — still completable with the env password.
    assert blocked_wall(_FakePage(body, file_inputs=0, create_acct=True)) is None
    # Guest form with resume upload must not be treated as login wall just for "Sign In" chrome.
    guest = "My Information\nFirst Name\nUpload Resume\nSubmit application"
    assert blocked_wall(_FakePage(guest, file_inputs=1)) is None
    jd = _FakePage(
        "Sign in\nCreate an account\nPrincipal Software Engineer\nHyderabad\nApply now",
        file_inputs=0,
    )
    jd.url = "https://boards.greenhouse.io/acme/jobs/1"
    assert blocked_wall(jd) is None
    assert is_sso_only_careers_url("https://www.amazon.jobs/en/search?base_query=architect")
    assert is_sso_only_careers_url("https://apply.careers.microsoft.com/careers?keywords=architect")
    assert not is_sso_only_careers_url("https://solera.wd5.myworkdayjobs.com/en-US/Global_Career_Site")
    assert is_hang_scan_url("https://higher.gs.com/results?keyword=architect")
    assert is_hang_scan_url("https://www.metacareers.com/jobs?q=architect&location=Hyderabad")
    assert not is_hang_scan_url("https://solera.wd5.myworkdayjobs.com/en-US/Global_Career_Site")


def test_indeed_oauth_url_is_login_wall():
    assert auth_wall_url(
        "https://secure.indeed.com/auth?oauth_client_id=abc&from=oauth&continue=https%3A%2F%2Fsecure.indeed.com"
    )
    assert auth_wall_url("https://accounts.google.com/gsi/button?client_id=x")
    assert auth_wall_url("https://passport.amazon.jobs/login")
    assert auth_wall_url("https://app.eightfold.ai/login?next=/careers")
    assert auth_wall_url("https://login.cognizant.com/oauth2")
    assert auth_wall_url("https://talent.cognizant.com/en_US/careers/Login2")
    assert not auth_wall_url("https://jobs.smartrecruiters.com/Experian/123-Solution-Architect")
    assert not auth_wall_url("https://app.eightfold.ai/careers/job?pid=123")
    page = _FakePage("Sign In | Indeed Accounts\nContinue with Google", file_inputs=0)
    page.url = "https://secure.indeed.com/auth?oauth_client_id=x"
    assert blocked_wall(page) == "login/account wall"


def test_hyland_icims_url():
    import json
    from pathlib import Path

    data = json.loads(Path(__file__).with_name("companies.json").read_text())
    hyland = next(c for c in data["companies"] if c["name"] == "Hyland")
    assert any("icims.com" in u and "in_iframe=1" in u for u in hyland["careersUrls"])
    intel = next(c for c in data["companies"] if c["name"] == "Intel")
    assert any("myworkdayjobs.com" in u for u in intel["careersUrls"])
    # URL may omit location=; pin_careers_hyderabad_location invents it every scan.
    byonder = next(c for c in data["companies"] if c["name"] == "Blue Yonder")
    assert any("search-results" in u for u in byonder["careersUrls"])
    href = "https://careers-hyland.icims.com/jobs/13991/senior-software-architect---.net/job?in_iframe=1"
    assert JOB_ID_HREF_RE.search(href)
    assert not JOB_ID_HREF_RE.search(
        "https://careers-hyland.icims.com/jobs/search?ss=1&searchKeyword=architect"
    )
    assert not JOB_ID_HREF_RE.search(
        "https://careers-hyland.icims.com/jobs/search?ss=1#icims_content_iframe"
    )
    from tools.hitechcity.careers_apply import CAPTCHA_PRONE_HOST_RE, _company_ats_rank

    assert CAPTCHA_PRONE_HOST_RE.search("https://jobs.smartrecruiters.com/Experian/1")
    assert _company_ats_rank({"careersUrls": ["https://careers-hyland.icims.com/jobs/search"]}) < (
        _company_ats_rank({"careersUrls": ["https://jobs.smartrecruiters.com/Experian/1"]})
    )


def test_attempt_ats_apply_persist_env_no_nameerror():
    """#206 persist-retry env read must not raise NameError for missing os."""
    from unittest.mock import MagicMock, patch

    page = MagicMock()
    with (
        patch("tools.ats.complete.complete_ats", return_value=("applied", "ok")),
        patch("tools.ats.complete.owner_asleep", return_value=True),
    ):
        status, reason = attempt_ats_apply(page, time_cap_s=5)
    assert status == "applied"
    assert reason == "ok"


def test_skip_uhg_default():
    import os

    prev_uhg = os.environ.get("HITECHCITY_SKIP_UHG")
    prev_names = os.environ.get("HITECHCITY_SKIP_COMPANIES")
    try:
        os.environ.pop("HITECHCITY_SKIP_UHG", None)
        os.environ.pop("HITECHCITY_SKIP_COMPANIES", None)
        assert company_skip_reason({"name": "Optum", "careersUrls": [
            "https://careers.unitedhealthgroup.com/search-jobs/Hyderabad/"
        ]}) == "skip_uhg"
        assert company_skip_reason({"name": "UnitedHealth Group", "careersUrls": []}) == "skip_uhg"
        assert is_uhg_skip_url("https://uhg.taleo.net/careersection/iam/accessmanagement/login.jsf")
        assert company_skip_reason({"name": "Hyland", "careersUrls": [
            "https://careers-hyland.icims.com/jobs/search"
        ]}) is None
        # Board allowlist must drop Optum/UHG by default (careers already skip them).
        from tools.hitechcity.campus_allowlist import write_allowlist_artifact
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            dest = Path(td) / "allow.json"
            write_allowlist_artifact(
                [
                    {"name": "Hyland"},
                    {"name": "Optum"},
                    {"name": "UnitedHealth Group"},
                    {"name": "Oracle"},
                ],
                dest=dest,
            )
            names = set(json.loads(dest.read_text())["names"])
            assert "Hyland" in names and "Oracle" in names
            assert "Optum" not in names and "UnitedHealth Group" not in names
            os.environ["HITECHCITY_SKIP_UHG"] = "0"
            write_allowlist_artifact([{"name": "Optum"}, {"name": "Hyland"}], dest=dest)
            names2 = set(json.loads(dest.read_text())["names"])
            assert "Optum" in names2 and "Hyland" in names2
        os.environ["HITECHCITY_SKIP_UHG"] = "0"
        assert company_skip_reason({"name": "Optum", "careersUrls": [
            "https://careers.unitedhealthgroup.com/search-jobs/Hyderabad/"
        ]}) is None
        assert not is_uhg_skip_url("https://uhg.taleo.net/careersection/iam/accessmanagement/login.jsf")
        os.environ["HITECHCITY_SKIP_COMPANIES"] = "Hyland,Solera"
        assert company_skip_reason({"name": "Hyland"}) == "skip_company"
        assert company_skip_reason({"name": "ModMed"}) is None
        assert JOB_ID_HREF_RE.search(
            "https://www.accenture.com/in-en/careers/jobdetails?id=ATCI-5721872-S2064313_en&title=Business+Capability+Architect"
        )
        assert JOB_ID_HREF_RE.search(
            "https://jobs.gartner.com/jobs/job/112613-executive-partner-enterprise-architecture-ea/"
        )
        # LinkedIn must honor the same skip (careers already did; LI used to burn Optum inventory).
        from tools.hitechcity.linkedin_target_apply import company_skip_reason as li_skip

        os.environ.pop("HITECHCITY_SKIP_UHG", None)
        assert li_skip({"name": "Optum", "careersUrls": []}) == "skip_uhg"
        assert li_skip({"name": "UnitedHealth Group", "careersUrls": []}) == "skip_uhg"
        assert li_skip({"name": "Oracle", "careersUrls": []}) is None
    finally:
        if prev_uhg is None:
            os.environ.pop("HITECHCITY_SKIP_UHG", None)
        else:
            os.environ["HITECHCITY_SKIP_UHG"] = prev_uhg
        if prev_names is None:
            os.environ.pop("HITECHCITY_SKIP_COMPANIES", None)
        else:
            os.environ["HITECHCITY_SKIP_COMPANIES"] = prev_names


def test_location_ui_skips_agentforce():
    assert not location_ui_input_meta_ok("Ask Agentforce anything search-field")
    assert not location_ui_input_meta_ok("oda-chat-input")
    assert location_ui_input_meta_ok("Location City or metro area")
    assert location_ui_input_meta_ok("Search jobs by city")


if __name__ == "__main__":
    test_title_ok()
    test_campus_location()
    test_oraclecloud_parent_card_location()
    test_careers_card_location()
    test_company_match()
    test_captcha_frame_ignores_hidden_badge()
    test_workday_create_account_is_completable()
    test_indeed_oauth_url_is_login_wall()
    test_hyland_icims_url()
    test_attempt_ats_apply_persist_env_no_nameerror()
    test_skip_uhg_default()
    test_location_ui_skips_agentforce()
    print("ok")
