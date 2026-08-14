#!/usr/bin/env python3
"""Small unit tests for Indeed skip / already-applied classifiers."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.indeed.uc_daily_apply import already_applied, skip_reason  # noqa: E402


def test_skip_hyd_remote_ok():
    assert skip_reason(
        "Solution Architect - Remote - Indeed.com",
        "Emgage",
        "Jobs at Emgage in Remote",
        "Find remote jobs in Bengaluru",
    ) is None
    assert skip_reason(
        "Technical Lead (.NET) - Hyderabad, Telangana - Indeed.com",
        "Lexicon",
        "Hyderabad, Telangana",
        "Find remote jobs",
    ) is None


def test_skip_bengaluru_not_overridden_by_snippet_remote():
    # Regression 2026-08-13: SERP chrome "Find remote jobs" must not keep
    # a Bengaluru-only posting (TechBiz Senior Full-Stack .NET Consultant).
    reason = skip_reason(
        "Senior Full-Stack .NET Consultant (Angular) - Bengaluru, Karnataka - Indeed.com",
        "TechBiz Global GmbH",
        "Full Stack Developer jobs in Bengaluru, Karnataka",
        "Find jobs\nFind remote jobs\nCompany reviews\nHyderabad also hiring",
    )
    assert reason == "location"


def test_skip_title_not_target():
    assert skip_reason(
        "Azure Integration Developer - Hyderabad, Telangana - Indeed.com",
        "Proclink",
        "Hyderabad, Telangana",
        "",
    ) == "title_not_target"


def test_enterprise_system_architect_ok():
    assert skip_reason(
        "Enterprise Architect - Commercial - Hyderabad, Telangana - Indeed.com",
        "Mattel",
        "Hyderabad, Telangana",
        "",
    ) is None
    assert skip_reason(
        "System Architect - Hyderabad, Telangana - Indeed.com",
        "Axiado",
        "Hyderabad, Telangana",
        "",
    ) is None


def test_skip_salesforce_service_cloud_title():
    # Regression 2026-08-14: "Success Architect(service cloud)" matched TITLE_OK via
    # architect…cloud and was Easy-Applied at Salesforce under Hitech City allowlist.
    assert skip_reason(
        "Success Architect(service cloud ) - Hyderabad District, Telangana - Indeed.com",
        "Salesforce",
        "Hyderabad District, Telangana",
        "",
    ) == "title_skip"
    assert skip_reason(
        "Solution Architect - Hyderabad, Telangana - Indeed.com",
        "Salesforce",
        "Hyderabad, Telangana",
        "",
    ) == "company_wrong_stack"
    # Keep .NET/Azure architect roles at Salesforce company.
    assert skip_reason(
        "Solution Architect (.NET / Azure) - Hyderabad, Telangana - Indeed.com",
        "Salesforce",
        "Hyderabad, Telangana",
        "",
    ) is None


def test_already_applied_job_view_only():
    assert already_applied("You applied to this job on 12 Aug", "https://in.indeed.com/viewjob?jk=abc")
    assert already_applied("You have already applied for this position", "https://in.indeed.com/viewjob?jk=abc")
    assert not already_applied(
        "Application submitted",
        "https://smartapply.indeed.com/beta/indeedapply/apply/questions",
    )


if __name__ == "__main__":
    test_skip_hyd_remote_ok()
    test_skip_bengaluru_not_overridden_by_snippet_remote()
    test_skip_title_not_target()
    test_enterprise_system_architect_ok()
    test_skip_salesforce_service_cloud_title()
    test_already_applied_job_view_only()
    print("ok")
