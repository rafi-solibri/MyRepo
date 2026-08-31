#!/usr/bin/env python3
"""Small unit tests for Indeed skip / already-applied classifiers."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.indeed.prepare_uc_profile import COPY_PATHS  # noqa: E402
from tools.indeed.uc_daily_apply import (  # noqa: E402
    already_applied,
    cookie_banner_visible_from_text,
    looks_anonymous_marketing_home,
    looks_login_wall,
    job_dedupe_key,
    looks_signed_in,
    skip_reason,
    want_from_question_text,
)


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


def test_skip_kochi_kerala_in_title():
    # Regression 2026-08-16: empty SERP location + "Kochi, Kerala" in title
    # was Easy-Applied (CogniCor) despite HARD Hyd/Remote-only rule.
    assert (
        skip_reason(
            "Senior / Lead Engineer (Full Stack) - Kochi, Kerala - Indeed.com",
            "CogniCor",
            "",
            "",
        )
        == "location"
    )
    # Remote still wins when present with another city.
    assert (
        skip_reason(
            "Senior C# Developer - Remote - Indeed.com",
            "Worklio",
            "we're expanding our development team in Chennai",
            "",
        )
        is None
    )


def test_already_applied_job_view_only():
    assert already_applied("You applied to this job on 12 Aug", "https://in.indeed.com/viewjob?jk=abc")
    assert already_applied("You have already applied for this position", "https://in.indeed.com/viewjob?jk=abc")
    # SmartApply duplicate interstitial must count as already applied.
    assert already_applied(
        "You have already applied to this job\nReturn to job search",
        "https://smartapply.indeed.com/beta/indeedapply/applybyapplyablejobid?indeedApplyableJobId=abc",
    )
    # Post-submit success copy must NOT be classified as already-applied.
    assert not already_applied(
        "Application submitted",
        "https://smartapply.indeed.com/beta/indeedapply/apply/questions",
    )


def test_hybrid_profile_copies_local_state():
    assert "Local State" in COPY_PATHS


def test_india_home_get_started_is_not_login_proof():
    home = (
        "Sign in\nYour next job starts here\n"
        "Create an account or sign in to see your personalised job recommendations.\n"
        "Get Started"
    )
    assert looks_anonymous_marketing_home(home)
    assert not looks_signed_in(home, "https://in.indeed.com/")
    assert not looks_login_wall(home, "https://in.indeed.com/")


def test_account_settings_and_serp_are_signed_in():
    account = (
        "Account settings\nYour contact information\n"
        "Manage your account security\nChange account type\n"
        "Messages Unread count 2"
    )
    assert looks_signed_in(account, "https://secure.indeed.com/settings/account")
    assert not looks_login_wall(account, "https://secure.indeed.com/settings/account")
    serp = (
        "Messages Unread count 2\n9+\nEmployers / Post Job\n"
        "Solutions Architect .NET jobs in Hyderabad, Telangana"
    )
    assert looks_signed_in(serp, "https://in.indeed.com/jobs?q=Solutions+Architect")
    wall = (
        "Sign In | Indeed Accounts\nReady to take the next step?\n"
        "Create an account or sign in.\nContinue with Apple\nEmail address *"
    )
    assert looks_login_wall(wall, "https://secure.indeed.com/auth?continue=https://myjobs.indeed.com/")
    assert not looks_signed_in(wall)


def test_company_ats_email_gate_is_not_indeed_login():
    """SAP / HCLTech careers cookie+email copy must not become indeed_login_required."""
    sap = (
        "We use cookies for the best user experience on our website.\n"
        "Accept All Cookies\nEnter your email address\nSign in to apply"
    )
    assert not looks_login_wall(sap, "https://career55.sapsf.eu/careers?company=HCLPRD")
    assert not looks_login_wall(
        "Continue with Apple\nEnter your email address",
        "https://careers.hcltech.com/job/Senior-Technical-Specialist",
    )


def test_cookie_banner_visible_from_text():
    # WSA/Crowe stuck screenshot 2026-08-31: OneTrust strip over Continue.
    assert cookie_banner_visible_from_text(
        "Cookies Settings\nReject All\nAccept All Cookies\nAnswer these questions"
    )
    assert cookie_banner_visible_from_text("Please Accept All Cookies to continue")
    assert not cookie_banner_visible_from_text(
        "Answer these questions from the employer\nContinue"
    )


def test_want_from_crowe_conflict_and_client_questions():
    # Crowe questions-module 2026-08-31 post-fix re-run: wrong Yes + current
    # employer on "work at Crowe client" blocked Continue (empty N/A follow-up).
    assert (
        want_from_question_text(
            "Do you have a familial (by blood or marriage), romantic, or "
            "close personal relationship with a Crowe employee or applicant?"
        )
        == "no"
    )
    assert (
        want_from_question_text(
            "Identify the individual(s), their role (if known) and describe "
            "the relationship (e.g., sibling, spouse, in-law, dating, roommate). "
            "If none, write N/A."
        )
        == "N/A"
    )
    assert (
        want_from_question_text(
            "Do you currently work at Crowe client? If yes, provide the company "
            "name. If no, reply No."
        )
        == "No"
    )
    assert (
        want_from_question_text(
            "Will you now or in the future require sponsorship to work? "
            "(i.e. Work Permit - Employment Visa (E Visa))"
        )
        == "no"
    )
    assert (
        want_from_question_text("Are you authorized to lawfully work in India?")
        == "yes"
    )
    assert (
        want_from_question_text("What is your current employer / company?")
        == "Nemetschek / Solibri"
    )


def test_job_dedupe_key_from_jk():
    assert job_dedupe_key("https://in.indeed.com/pagead/clk?jk=abc123def456&from=serp", "") == "abc123def456"
    assert job_dedupe_key("https://in.indeed.com/viewjob?jk=abc123def456", "other") == "abc123def456"
    assert job_dedupe_key("https://in.indeed.com/viewjob?jk=abc123def456", "") == "abc123def456"
    assert job_dedupe_key("https://in.indeed.com/rc/clk?from=serp", "deadbeef") == "deadbeef"
    # Encoded continueUrl / vjk used by pagead hops (PanApps 11× repeat 2026-08-24).
    assert (
        job_dedupe_key(
            "https://in.indeed.com/pagead/clk?vjk=2eb38af35baf1fdc&from=serp",
            "",
        )
        == "2eb38af35baf1fdc"
    )
    assert (
        job_dedupe_key(
            "https://in.indeed.com/rc/clk?continueUrl=https%3A%2F%2Fin.indeed.com%2Fviewjob%3Fjk%3D2eb38af35baf1fdc",
            "",
        )
        == "2eb38af35baf1fdc"
    )


if __name__ == "__main__":
    test_skip_hyd_remote_ok()
    test_skip_bengaluru_not_overridden_by_snippet_remote()
    test_skip_title_not_target()
    test_enterprise_system_architect_ok()
    test_skip_salesforce_service_cloud_title()
    test_skip_kochi_kerala_in_title()
    test_already_applied_job_view_only()
    test_hybrid_profile_copies_local_state()
    test_india_home_get_started_is_not_login_proof()
    test_account_settings_and_serp_are_signed_in()
    test_cookie_banner_visible_from_text()
    test_want_from_crowe_conflict_and_client_questions()
    test_job_dedupe_key_from_jk()
    print("ok")
