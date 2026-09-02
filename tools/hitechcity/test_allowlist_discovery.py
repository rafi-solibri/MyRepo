#!/usr/bin/env python3
"""Tests for campus allowlist + discovery merge."""

from __future__ import annotations

import json
import os
from pathlib import Path

from tools.hitechcity.campus_allowlist import (
    company_allowed,
    reset_allowlist_cache,
    write_allowlist_artifact,
)
from tools.hitechcity.campus_tenant_catalog import (
    CAMPUS_DEFINITIONS,
    CAMPUS_TENANT_CATALOG,
    PREFERRED_HOME_CAMPUSES,
    canonicalize_tenant_name,
    campus_preference_rank,
    fetch_web_directory_tenants,
    _parse_mindspace_top_tenants,
    _parse_cityinfo_tenants,
)
from tools.hitechcity.discover_tenants import (
    DISCOVERY_SEEDS,
    _is_junk_tenant,
    _merge_candidate,
    discover_from_campus_catalog,
    discover_from_seeds,
    prune_junk_tenants,
)


def test_allowlist_match(tmp_path: Path | None = None):
    reset_allowlist_cache()
    art = Path("/tmp/hitechcity-allowlist-test.json")
    write_allowlist_artifact(
        [{"name": "Microsoft"}, {"name": "JPMorgan Chase"}, {"name": "Palo Alto Networks"}],
        art,
    )
    os.environ["HITECHCITY_COMPANY_ALLOWLIST"] = str(art)
    reset_allowlist_cache()
    assert company_allowed("Microsoft India")
    assert company_allowed("J.P. Morgan")
    assert company_allowed("Palo Alto Networks")
    assert not company_allowed("Random Hyd Startup Pvt Ltd")
    del os.environ["HITECHCITY_COMPANY_ALLOWLIST"]
    reset_allowlist_cache()
    assert company_allowed("Anyone")  # no filter


def test_discovery_seeds_merge():
    companies = [
        {
            "name": "Microsoft",
            "campuses": ["sattva-knowledge-city"],
            "linkedinSlug": "microsoft",
            "careersUrls": ["https://example.com"],
            "priority": 1,
        }
    ]
    before = len(companies)
    stats = discover_from_seeds(companies)
    assert len(companies) > before
    assert "HighRadius" in stats["added"] or any(c["name"] == "HighRadius" for c in companies)
    # Idempotent second pass should not duplicate Microsoft
    status = _merge_candidate(
        companies,
        {"name": "Microsoft", "campuses": ["mindspace-madhapur"], "linkedinSlug": "microsoft"},
        "seed",
    )
    assert status == "updated"
    ms = next(c for c in companies if c["name"] == "Microsoft")
    assert "mindspace-madhapur" in ms["campuses"]
    assert len(DISCOVERY_SEEDS) >= 10


def test_discovery_junk_rejected_and_pruned():
    companies = [
        {
            "name": "Microsoft",
            "campuses": ["sattva-knowledge-city"],
            "linkedinSlug": "microsoft",
            "careersUrls": ["https://example.com"],
            "priority": 1,
            "source": "seed",
        },
        {
            "name": "software companies erbil",
            "campuses": ["sattva-knowledge-city"],
            "linkedinSlug": "software-companies-erbil",
            "careersUrls": [],
            "priority": 2,
            "source": "linkedin_search",
        },
        {
            "name": "Hyderabad Tech Community",
            "campuses": ["sattva-knowledge-city"],
            "linkedinSlug": "hyderabad-tech-community",
            "careersUrls": [],
            "priority": 2,
            "source": "linkedin_search",
        },
    ]
    assert _is_junk_tenant("software companies erbil", "software-companies-erbil")
    assert _merge_candidate(
        companies,
        {
            "name": "software companies erbil",
            "linkedinSlug": "software-companies-erbil",
            "campuses": ["sattva-knowledge-city"],
        },
        "linkedin_search",
    ) is None
    removed = prune_junk_tenants(companies)
    assert "software companies erbil" in removed
    assert "Hyderabad Tech Community" in removed
    assert any(c["name"] == "Microsoft" for c in companies)
    assert not any("erbil" in (c.get("name") or "").lower() for c in companies)


def test_allowlist_js_module_exists():
    p = Path(__file__).with_name("campus_allowlist.js")
    assert p.is_file()
    text = p.read_text(encoding="utf-8")
    assert "companyAllowed" in text
    assert "HITECHCITY_COMPANY_ALLOWLIST" in text


def test_campus_catalog_covers_priority_parks():
    assert len(CAMPUS_TENANT_CATALOG) >= 60
    camps = {c for row in CAMPUS_TENANT_CATALOG for c in row["campuses"]}
    assert "mindspace-madhapur" in camps  # Raheja
    assert "sattva-knowledge-city" in camps
    assert "sattva-knowledge-park" in camps
    assert "rmz-nexity" in camps
    assert "rmz-skyview" in camps
    assert "rmz-futura" in camps
    names = {row["name"] for row in CAMPUS_TENANT_CATALOG}
    assert "HighRadius" in names
    assert "Vanguard" in names
    assert "Apple" in names
    assert "Electronic Arts" in names
    assert "CGI" in names
    assert "EY" in names
    assert canonicalize_tenant_name("Highradius") == "HighRadius"
    assert canonicalize_tenant_name("Xilinx India Technology Services") == "AMD"
    assert canonicalize_tenant_name("OTIS Elevator Company") is None
    assert canonicalize_tenant_name("Ernst & Young") == "EY"
    assert canonicalize_tenant_name("EA Sports") == "Electronic Arts"
    assert campus_preference_rank({"campuses": ["rmz-nexity"]}) == 0
    assert campus_preference_rank({"campuses": ["dlf-cyber-city"]}) == 1
    assert any(c["id"] == "rmz-nexity" for c in CAMPUS_DEFINITIONS)
    assert PREFERRED_HOME_CAMPUSES >= {
        "sattva-knowledge-city",
        "mindspace-madhapur",
        "rmz-nexity",
        "rmz-skyview",
    }


def test_discover_from_campus_catalog_adds_knowledge_park():
    companies: list[dict] = []
    stats = discover_from_campus_catalog(companies)
    assert stats["added"]
    assert any(c["name"] == "Vanguard" for c in companies)
    kp = [c for c in companies if "sattva-knowledge-park" in (c.get("campuses") or [])]
    assert len(kp) >= 4


def test_parse_mindspace_and_cityinfo_html():
    ms_html = """
    <h2>Top Tenants</h2>
    <ul><li>Cognizant</li><li>Highradius</li><li>AMD</li></ul>
    <p>(On the basis of % of Gross Rentals)</p>
    <h3>Location Highlights</h3>
    """
    assert "HighRadius" in _parse_mindspace_top_tenants(ms_html)
    assert "AMD" in _parse_mindspace_top_tenants(ms_html)
    ci = (
        "<p>The current tenants of this building are Apple India, Blue Yonder India "
        "(JDA Software), and Intel Technology India. Related Projects Foo</p>"
    )
    parsed = _parse_cityinfo_tenants(ci)
    assert "Apple" in parsed
    assert "Blue Yonder" in parsed
    assert "Intel" in parsed
    sky = (
        "<p>The present tenants in this facility are Qualcomm, CGI Information Systems "
        "and Management Consultants, LTI Mindtree, and Providence Global Center. "
        "Related Projects Foo</p>"
    )
    sky_parsed = _parse_cityinfo_tenants(sky)
    assert "Qualcomm" in sky_parsed
    assert "CGI" in sky_parsed
    assert "Providence" in sky_parsed
    jpmc = (
        "<p>The current tenant of this building is J.P. Morgan India. "
        "Related Projects Salarpuria</p>"
    )
    assert "JPMorgan Chase" in _parse_cityinfo_tenants(jpmc)


def test_openings_preference_and_hints():
    from tools.hitechcity.openings_probe import (
        CAREERS_URL_HINTS,
        ensure_careers_url_hints,
        openings_preference_rank,
    )

    assert openings_preference_rank({"hasOpenings": True}) == 0
    assert openings_preference_rank({"openingsCount": 2}) == 0
    assert openings_preference_rank({}) == 1
    assert "Electronic Arts" in CAREERS_URL_HINTS
    assert "CGI" in CAREERS_URL_HINTS
    assert "fluttergroup.com" in CAREERS_URL_HINTS["Flutter Entertainment"][0]
    assert "ltm.com" in CAREERS_URL_HINTS["LTIMindtree"][0]
    assert "providence.jobs" in CAREERS_URL_HINTS["Providence"][0]
    assert "greenhouse.io/storableindia" in CAREERS_URL_HINTS["Storable"][0]
    companies = [
        {"name": "Electronic Arts", "campuses": ["rmz-nexity"], "careersUrls": []},
        {"name": "Someone Else", "campuses": ["dlf-cyber-city"], "careersUrls": []},
        {
            "name": "Flutter Entertainment",
            "campuses": ["rmz-nexity"],
            "careersUrls": [
                "https://careers.flutter.com/search/?q=Engineering+Manager&locationsearch=Hyderabad"
            ],
        },
        {
            "name": "Providence",
            "campuses": ["rmz-nexity"],
            "careersUrls": [
                "https://www.providenceindia.com/careers",
                "https://careers.providence.org/us/en/search-results?keywords=Engineering%20Manager",
            ],
        },
        {
            "name": "LTIMindtree",
            "campuses": ["mindspace-madhapur"],
            "careersUrls": [
                "https://careers.ltimindtree.com/search/?q=Engineering+Manager&locationsearch=Hyderabad"
            ],
        },
        {
            "name": "Storable",
            "campuses": ["mindspace-madhapur"],
            "careersUrls": ["https://www.storable.com/careers/"],
        },
    ]
    touched = ensure_careers_url_hints(companies)
    assert "Electronic Arts" in touched
    assert companies[0]["careersUrls"]
    assert not companies[1].get("careersUrls")
    assert all("flutter.com/" not in u for u in companies[2]["careersUrls"])
    assert any("fluttergroup.com" in u for u in companies[2]["careersUrls"])
    assert all("careers.providence.org" not in u and "providenceindia.com" not in u for u in companies[3]["careersUrls"])
    assert any("providence.jobs" in u for u in companies[3]["careersUrls"])
    assert all("careers.ltimindtree.com" not in u for u in companies[4]["careersUrls"])
    assert any("ltm.com" in u for u in companies[4]["careersUrls"])
    assert all("storable.com/careers/" not in u for u in companies[5]["careersUrls"])
    assert any("greenhouse.io/storableindia" in u for u in companies[5]["careersUrls"])


if __name__ == "__main__":
    test_allowlist_match()
    test_discovery_seeds_merge()
    test_discovery_junk_rejected_and_pruned()
    test_allowlist_js_module_exists()
    test_campus_catalog_covers_priority_parks()
    test_discover_from_campus_catalog_adds_knowledge_park()
    test_parse_mindspace_and_cityinfo_html()
    test_openings_preference_and_hints()
    print("ok")
