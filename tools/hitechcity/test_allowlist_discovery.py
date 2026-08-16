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
from tools.hitechcity.discover_tenants import (
    DISCOVERY_SEEDS,
    _is_junk_tenant,
    _merge_candidate,
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
    # Seeds must fill empty careersUrls so careers-only runs can open Greenhouse/Workday.
    hr = next(c for c in companies if c["name"] == "HighRadius")
    assert any("highradius.com" in u for u in (hr.get("careersUrls") or []))
    empty_hr = [{"name": "HighRadius", "campuses": ["mindspace-madhapur"], "linkedinSlug": "highradius", "careersUrls": []}]
    assert _merge_candidate(
        empty_hr,
        {
            "name": "HighRadius",
            "linkedinSlug": "highradius",
            "careersUrls": ["https://www.highradius.com/about/career/"],
        },
        "seed",
    ) == "updated"
    assert empty_hr[0]["careersUrls"] == ["https://www.highradius.com/about/career/"]


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


if __name__ == "__main__":
    test_allowlist_match()
    test_discovery_seeds_merge()
    test_discovery_junk_rejected_and_pruned()
    test_allowlist_js_module_exists()
    print("ok")
