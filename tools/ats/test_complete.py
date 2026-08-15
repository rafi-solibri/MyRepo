#!/usr/bin/env python3
"""Unit checks for shared ATS completion (no browser)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.ats.complete import (
    auth_wall_reason,
    classify_ats_host,
    frame_url_is_captcha_challenge,
    iframe_box_is_onscreen,
    is_board_tracking_url,
    is_hard_ats_wall,
    is_submitted_text,
    is_unavailable_text,
)


def assert_true(cond, msg):
    if not cond:
        raise AssertionError(msg)


assert_true(is_submitted_text("Thank you for applying to Acme"), "thank-you must count")
assert_true(is_submitted_text("Your application was sent"), "sent must count")
assert_true(is_submitted_text("We have received your application"), "received must count")
assert_true(is_submitted_text("Thanks for your interest — you're all set"), "all-set must count")
assert_true(not is_submitted_text("Apply now to submit your application"), "CTA text must not count")

assert_true(is_hard_ats_wall("CAPTCHA/bot wall"), "captcha is hard")
assert_true(is_hard_ats_wall("ats_login_wall"), "login is hard")
assert_true(not is_hard_ats_wall("external_incomplete_or_timeout"), "timeout is not a company wall")
assert_true(not is_hard_ats_wall("ats_time_cap"), "time_cap is not a company wall")
assert_true(not is_hard_ats_wall("stuck/time cap after 3 steps"), "stuck is not a company wall")
assert_true(not is_hard_ats_wall("job_unavailable"), "maintenance is not a company wall")
assert_true(not is_hard_ats_wall("did_not_leave_indeed"), "tracking hop is not a company wall")

assert_true(classify_ats_host("https://acme.wd1.myworkdayjobs.com/en-US/job") == "workday", "wd host")
assert_true(classify_ats_host("https://boards.greenhouse.io/acme/jobs/1") == "greenhouse", "gh host")
assert_true(classify_ats_host("https://jobs.lever.co/acme/abc") == "greenhouse", "lever grouped")
assert_true(classify_ats_host("https://acme.icims.com/jobs/1") == "greenhouse", "icims grouped")
assert_true(classify_ats_host("https://login.microsoftonline.com/xyz") == "sso", "sso host")
assert_true(classify_ats_host("https://www.linkedin.com/jobs/view/1") == "linkedin", "li host")
assert_true(classify_ats_host("https://careers.acme.com/apply") == "generic", "generic host")
assert_true(
    classify_ats_host("https://community.workday.com/maintenance-page") == "unavailable",
    "workday maintenance host",
)
assert_true(classify_ats_host("https://www.indeed.com/applystart?jk=1") == "indeed", "indeed hop")
assert_true(is_board_tracking_url("https://www.indeed.com/applystart?jk=abc"), "applystart tracking")
assert_true(is_board_tracking_url("https://www.indeed.com/rc/clk?jk=abc"), "rc/clk tracking")
assert_true(not is_board_tracking_url("https://acme.wd1.myworkdayjobs.com/en-US/job"), "wd not tracking")
assert_true(is_unavailable_text("We'll be back shortly — scheduled maintenance"), "maint text")
assert_true(is_submitted_text("Thanks for applying — we've got your application"), "got-app must count")

assert_true(frame_url_is_captcha_challenge("https://www.google.com/recaptcha/api2/bframe?x=1"), "bframe")
assert_true(not frame_url_is_captcha_challenge("https://www.google.com/recaptcha/api2/anchor"), "hidden badge")
assert_true(iframe_box_is_onscreen({"width": 300, "height": 140}), "onscreen box")
assert_true(not iframe_box_is_onscreen({"width": 0, "height": 0}), "hidden 0x0")

# Workday Create Account is completable — not a hard wall when email+password exist.
os.environ["WORKDAY_PASSWORD"] = "x" * 12
assert_true(
    auth_wall_reason(
        "https://acme.wd5.myworkdayjobs.com/en-US/Apply",
        "Create Account / Sign In  Current step 1 of 5",
        has_password=True,
        has_file=False,
        has_workday_apply=True,
        has_email_field=True,
    )
    is None,
    "Workday create-account must not be treated as login wall",
)

assert_true(
    auth_wall_reason(
        "https://login.microsoftonline.com/common/oauth2",
        "Sign in",
        has_password=True,
        has_file=False,
    )
    == "ats_login_wall",
    "Azure B2C / Microsoft SSO is a hard wall",
)

assert_true(
    auth_wall_reason(
        "https://boards.greenhouse.io/acme/jobs/1",
        "Apply for this job",
        has_password=False,
        has_file=True,
    )
    is None,
    "Greenhouse with resume input is guest-applyable",
)

assert_true(
    auth_wall_reason(
        "https://careers.acme.com/job",
        "This position has been filled",
        has_file=True,
    )
    == "job_unavailable",
    "closed requisition",
)

print("tools/ats/test_complete.py OK")
