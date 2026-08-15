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
    ats_password,
    auth_wall_reason,
    classify_ats_host,
    extract_hop_destination_from_url,
    extract_offsite_from_text,
    frame_url_is_captcha_challenge,
    iframe_box_is_onscreen,
    is_board_tracking_url,
    is_brochure_or_dead_end,
    is_hard_ats_wall,
    is_submitted_text,
    is_unavailable_text,
    looks_like_apply_cta,
    page_fingerprint,
    workday_on_standalone_login,
    workday_password_alert,
    workday_password_rejected,
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
assert_true(not is_hard_ats_wall("no_ats_form"), "brochure miss is not a company wall")
assert_true(not looks_like_apply_cta("View applied jobs (20+)"), "naukri chrome is not Apply")
assert_true(not looks_like_apply_cta("Applied jobs"), "applied-jobs chrome is not Apply")
assert_true(looks_like_apply_cta("Apply now"), "Apply now is a real CTA")
assert_true(looks_like_apply_cta("Apply for this job"), "Apply for this job is a real CTA")
assert_true(looks_like_apply_cta("Quick apply"), "Quick apply is a real CTA")
assert_true(
    is_brochure_or_dead_end(
        "https://www.mihira.ai/careers.html",
        "Join our growing team. See all open roles.",
    ),
    "marketing careers.html is brochure",
)
assert_true(
    not is_brochure_or_dead_end(
        "https://boards.greenhouse.io/acme/jobs/1",
        "Apply for this job\nFirst name\nUpload resume",
        has_file=True,
    ),
    "Greenhouse form is not brochure",
)
assert_true(
    extract_hop_destination_from_url(
        "https://www.indeed.com/applystart?jk=abc&continueUrl=https%3A%2F%2Facme.wd1.myworkdayjobs.com%2Fen-US%2Fjob"
    )
    == "https://acme.wd1.myworkdayjobs.com/en-US/job",
    "Indeed applystart dest",
)
assert_true(
    extract_offsite_from_text(
        '{"companyApplyUrl":"https://acme.wd5.myworkdayjobs.com/en-US/Apply"}'
    )
    == "https://acme.wd5.myworkdayjobs.com/en-US/Apply",
    "LinkedIn companyApplyUrl",
)
assert_true(
    not extract_offsite_from_text('{"companyApplyUrl":"https://www.linkedin.com/jobs/view/1"}'),
    "reject LinkedIn self-url",
)
assert_true(classify_ats_host("https://app.eightfold.ai/careers/job?pid=1") == "greenhouse", "eightfold is ATS")
assert_true(
    classify_ats_host("https://login.microsoftonline.com/cognizant") == "sso",
    "cognizant SSO host",
)

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
assert_true(is_unavailable_text("403 Forbidden"), "http 403 is unavailable")
assert_true(is_submitted_text("Thanks for applying — we've got your application"), "got-app must count")


class _FpPage:
    def __init__(self, url: str, text: str):
        self.url = url
        self._text = text

    def locator(self, sel: str):
        page = self

        class _Body:
            def inner_text(self, *a, **k):
                return page._text

        return _Body()


_fp_a = page_fingerprint(_FpPage("https://apply.careers.microsoft.com/careers/apply?pid=1", "Apply now"))
_fp_b = page_fingerprint(_FpPage("https://apply.careers.microsoft.com/careers/apply?pid=1", "Apply now"))
_fp_c = page_fingerprint(_FpPage("https://apply.careers.microsoft.com/careers/apply?pid=1", "Thank you for applying"))
assert_true(_fp_a == _fp_b, "same page fingerprint")
assert_true(_fp_a != _fp_c, "changed body changes fingerprint")

assert_true(frame_url_is_captcha_challenge("https://www.google.com/recaptcha/api2/bframe?x=1"), "bframe")
assert_true(not frame_url_is_captcha_challenge("https://www.google.com/recaptcha/api2/anchor"), "hidden badge")
assert_true(iframe_box_is_onscreen({"width": 300, "height": 140}), "onscreen box")
assert_true(not iframe_box_is_onscreen({"width": 0, "height": 0}), "hidden 0x0")

# The one owner secret (NAUKRI_WORKDAY_PASSWORD) must satisfy ats_password().
for k in ("WORKDAY_PASSWORD", "ATS_PASSWORD", "NAUKRI_ATS_PASSWORD", "LINKEDIN_PASSWORD"):
    os.environ.pop(k, None)
os.environ["NAUKRI_WORKDAY_PASSWORD"] = "owner-secret-18chars"
assert_true(ats_password() == "owner-secret-18chars", "NAUKRI_WORKDAY_PASSWORD is the owner password")
assert_true(os.environ.get("WORKDAY_PASSWORD") == "owner-secret-18chars", "alias WORKDAY_PASSWORD")

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
        "https://boards.greenhouse.io/acme/jobs/1",
        "Sign in\nCreate an account\nApply for this job\nHyderabad",
        has_password=False,
        has_file=False,
    )
    is None,
    "Greenhouse JD chrome Create an account is not a login wall",
)

assert_true(
    workday_password_rejected(
        "Error: Password must include:\n\t  - An uppercase character\n\t  - A numeric character"
    ),
    "Solera Workday password-rule error is a reject",
)
assert_true(not workday_password_rejected("Password*\nVerify New Password*"), "labels are not a reject")
assert_true(
    not workday_password_rejected(
        "Password Requirements:\n\nA special character\nAn uppercase character\nA numeric character"
    ),
    "static Password Requirements list is not a reject",
)
_chrome = "Skip to main content\nSign In\n" + ("step 1 of 7 Create Account/Sign In\n" * 50)
assert_true(
    workday_password_rejected(
        _chrome + "Error: Password must include:\n\t  - An uppercase character"
    ),
    "password reject still matches after Workday progress-bar chrome",
)


class _AlertPage:
    def __init__(self, alert: str | None, body: str):
        self._alert = alert
        self._text = body

    def locator(self, sel: str):
        page = self

        class _El:
            def count(self):
                if "inputAlert" in sel:
                    return 1 if page._alert else 0
                return 1

            def is_visible(self):
                if "inputAlert" in sel:
                    return bool(page._alert)
                return True

            def inner_text(self, *a, **k):
                if "inputAlert" in sel:
                    return page._alert or ""
                return page._text

            @property
            def first(self):
                return self

        return _El()


assert_true(
    workday_password_alert(
        _AlertPage("Error: Password must include:\n  - An uppercase character", _chrome)
    ),
    "inputAlert password reject wins over chrome-heavy body",
)
assert_true(
    workday_password_alert(
        _AlertPage(None, _chrome + "Error: Password must include:\n  - A numeric character")
    ),
    "long body still sees password reject past a 1500-char slice",
)
assert_true(
    not workday_password_alert(_AlertPage(None, _chrome + "Password*\nVerify New Password*")),
    "labels alone are not a live reject",
)
assert_true(
    workday_on_standalone_login(
        "https://solera.wd5.myworkdayjobs.com/en-US/Global_Career_Site/login?redirect=%2Fjob"
    ),
    "Workday /login is standalone auth",
)
assert_true(
    not workday_on_standalone_login(
        "https://solera.wd5.myworkdayjobs.com/en-US/Global_Career_Site/job/Hyderabad/Principal-Software-Engineer_JR-1/apply/autofillWithResume"
    ),
    "in-flow apply URL is not standalone login",
)

assert_true(
    classify_ats_host("https://talent.cognizant.com/en_US/careers/Login2") == "sso",
    "Cognizant talent login2 is SSO",
)
assert_true(
    auth_wall_reason(
        "https://careers.qualcomm.com/careers/apply?pid=446720272187",
        "Sign In\nCurrent Qualcomm employees must sign in using the Career Hub.\n"
        "Email\nWe don't recognize this email. Create a new account\n"
        "Continue\nOR\nSign in using Google\nFirst time here?\nCreate an account",
        has_password=False,
        has_file=False,
        has_email_field=True,
    )
    == "ats_login_wall",
    "Eightfold email-only Sign-in is a hard wall",
)
assert_true(
    auth_wall_reason(
        "https://careers.qualcomm.com/careers/apply?pid=1",
        "Sign in using Google\nCreate an account",
        has_password=False,
        has_file=True,
        has_email_field=True,
    )
    is None,
    "Resume upload means guest apply can continue",
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

# Microsoft Eightfold careers: SSO buttons, no password, no resume input.
ms_chooser = (
    "Select a method below to Sign in. This allows you to access your profile "
    "or begin a new application. Sign in using Microsoft Sign in using LinkedIn "
    "Sign in using Google. If you are a Microsoft Employee, Sign in here."
)
assert_true(
    auth_wall_reason(
        "https://apply.careers.microsoft.com/careers/apply?pid=1",
        ms_chooser,
        has_password=False,
        has_file=False,
    )
    == "ats_login_wall",
    "Microsoft Eightfold SSO chooser (no password) is a hard wall",
)

print("tools/ats/test_complete.py OK")
