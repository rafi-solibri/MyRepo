#!/usr/bin/env python3
"""Unit checks for shared ATS completion (no browser)."""
from __future__ import annotations

import os
import re
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
    complete_icims,
    icims_hcaptcha_login,
    apply_form_still_open,
    visible_captcha_challenge,
    icims_logged_in,
    icims_should_wait_captcha,
    iframe_box_is_onscreen,
    is_board_tracking_url,
    is_brochure_or_dead_end,
    is_hard_ats_wall,
    is_submitted_text,
    is_unavailable_text,
    looks_like_apply_cta,
    page_fingerprint,
    resolve_ats_cdp,
    ALREADY_APPLIED_RE,
    SUBMITTED_RE,
    workday_compliant_password,
    workday_on_standalone_login,
    workday_password_alert,
    workday_password_rejected,
    workday_stuck_on_sign_in,
)


def assert_true(cond, msg):
    if not cond:
        raise AssertionError(msg)


assert_true(is_submitted_text("Thank you for applying to Acme"), "thank-you must count")
assert_true(is_submitted_text("Your application was sent"), "sent must count")
assert_true(is_submitted_text("We have received your application"), "received must count")
assert_true(is_submitted_text("Thanks for your interest — you're all set"), "all-set must count")
assert_true(not is_submitted_text("Apply now to submit your application"), "CTA text must not count")

# Indeed UC owns :9222 — ATS must opt into owned Chromium via cdp="0" / ATS_CDP=0.
_prev_ats = os.environ.pop("ATS_CDP", None)
_prev_li = os.environ.pop("LINKEDIN_CDP", None)
try:
    assert_true(resolve_ats_cdp("0") is None, "cdp=0 must force owned browser")
    assert_true(resolve_ats_cdp("off") is None, "cdp=off must force owned browser")
    assert_true(
        resolve_ats_cdp("http://127.0.0.1:9222") == "http://127.0.0.1:9222",
        "explicit CDP URL must pass through",
    )
    assert_true(
        resolve_ats_cdp(None) == "http://127.0.0.1:9222",
        "unset default remains LinkedIn-compatible :9222",
    )
    os.environ["ATS_CDP"] = "0"
    assert_true(resolve_ats_cdp(None) is None, "ATS_CDP=0 must force owned browser")
finally:
    if _prev_ats is None:
        os.environ.pop("ATS_CDP", None)
    else:
        os.environ["ATS_CDP"] = _prev_ats
    if _prev_li is None:
        os.environ.pop("LINKEDIN_CDP", None)
    else:
        os.environ["LINKEDIN_CDP"] = _prev_li


# Oracle Cloud My Profile after apply
from tools.ats.complete import looks_submitted as _looks_submitted
from tools.ats import complete as _complete_mod

class _OraclePage:
    url = "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/my-profile"
    def __init__(self, text):
        self._text = text

_orig_body = _complete_mod._body
_complete_mod._body = lambda page, limit=4000: getattr(page, "_text", "")[:limit]
try:
    assert_true(
        _looks_submitted(
            _OraclePage(
                "MY APPLICATIONS\nACTIVE JOB APPLICATIONS\nManager\nHyderabad\nStatus\nUnder Consideration\nApplied on 16/08/2026"
            )
        ),
        "Oracle Under Consideration on my-profile must count as submitted",
    )
    assert_true(
        not _looks_submitted(_OraclePage("Apply now to join our team")),
        "generic apply text must not count",
    )
finally:
    _complete_mod._body = _orig_body

assert_true(is_hard_ats_wall("CAPTCHA/bot wall"), "captcha is hard")
assert_true(is_hard_ats_wall("ats_login_wall"), "login is hard")
assert_true(is_hard_ats_wall("ats_otp_wall"), "oracle email OTP is hard wall")
assert_true(is_hard_ats_wall("verification code was sent"), "otp phrase is hard wall")
assert_true(not is_hard_ats_wall("external_incomplete_or_timeout"), "timeout is not a company wall")
assert_true(not is_hard_ats_wall("easy_apply_incomplete"), "easy incomplete is not a company wall")
from tools.ats.complete import otp_wall_reason
assert_true(
    otp_wall_reason(
        "Confirm Your Identity\nThe verification code was sent to this email address: a@b.com"
    )
    == "ats_otp_wall",
    "Oracle Confirm Your Identity is OTP wall",
)
assert_true(
    otp_wall_reason("Email Address\nI agree with the terms and conditions\nNEXT") is None,
    "Oracle email gate alone is not OTP wall",
)
assert_true(
    auth_wall_reason(
        "https://careers.oracle.com/en/sites/jobsearch/job/1/apply/email",
        "Confirm Your Identity\nThe verification code was sent",
        has_file=True,
        has_email_field=True,
    )
    == "ats_otp_wall",
    "OTP beats has_file guest continue",
)
from tools.ats.complete import owner_form_wait_sec, owner_asleep, persist_retry_burst_sec
_saved_form = {k: os.environ.get(k) for k in ("ATS_OWNER_FORM_WAIT_SEC", "ATS_CAPTCHA_WAIT_SEC", "HOME_LOCAL", "CHROME_HEADLESS", "HITECHCITY_OWNER_ASLEEP", "ATS_PERSIST_RETRY_SEC", "HITECHCITY_ATS_PERSIST_RETRY")}
for k in ("ATS_OWNER_FORM_WAIT_SEC", "ATS_CAPTCHA_WAIT_SEC", "HOME_LOCAL", "CHROME_HEADLESS", "HITECHCITY_OWNER_ASLEEP", "ATS_PERSIST_RETRY_SEC", "HITECHCITY_ATS_PERSIST_RETRY"):
    os.environ.pop(k, None)
# Isolate from live overnight flag files left by the daily cron.
_asleep_flags = []
for _p in ("/tmp/hitechcity-owner-asleep", "/tmp/ats-owner-asleep"):
    _path = Path(_p)
    if _path.exists():
        _bak = Path(_p + ".testbak")
        _path.rename(_bak)
        _asleep_flags.append((_path, _bak))
try:
    os.environ["HOME_LOCAL"] = "1"
    assert_true(owner_form_wait_sec() >= 180, "headed owner form wait defaults on")
    os.environ["ATS_OWNER_FORM_WAIT_SEC"] = "0"
    assert_true(owner_form_wait_sec() == 0, "explicit 0 disables owner form wait")
    os.environ.pop("ATS_OWNER_FORM_WAIT_SEC", None)
    os.environ["HITECHCITY_OWNER_ASLEEP"] = "1"
    assert_true(owner_asleep(), "OWNER_ASLEEP env detected")
    assert_true(owner_form_wait_sec() == 12, "owner-asleep form wait is short park")
    assert_true(persist_retry_burst_sec() == 12, "owner-asleep persist burst is short")
    os.environ["HITECHCITY_ATS_PERSIST_RETRY"] = "0"
    assert_true(persist_retry_burst_sec() == 12, "persist_retry=0 still parks briefly")
    os.environ["ATS_PERSIST_RETRY_SEC"] = "0"
    assert_true(persist_retry_burst_sec() == 0, "explicit persist retry 0 disables burst")
finally:
    for _path, _bak in _asleep_flags:
        if _bak.exists():
            _bak.rename(_path)
for k, v in _saved_form.items():
    if v is None:
        os.environ.pop(k, None)
    else:
        os.environ[k] = v
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
assert_true(
    classify_ats_host("https://login.ibm.com/authsvc/mtfim/sps/authsvc?PolicyId=x") == "sso",
    "IBMid login.ibm.com is SSO fail-fast",
)
assert_true(
    not is_brochure_or_dead_end(
        "https://www.storable.com/about-us/culture/careers/?gh_jid=5564835004",
        "Explore Storable Careers. View Current Openings.",
    ),
    "gh_jid marketing embed is a job detail, not brochure",
)
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
        "https://login.ibm.com/authsvc/mtfim/sps/authsvc",
        "Sign in or create an IBMid",
        has_password=True,
        has_file=False,
    )
    == "ats_login_wall",
    "IBMid login.ibm.com is a hard wall",
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


class _SignInPage:
    def __init__(self, title: str, *, sign_in: bool = True, app_fields: bool = False):
        self._title = title
        self._sign_in = sign_in
        self._app = app_fields
        self.url = (
            "https://gartner.wd5.myworkdayjobs.com/en-US/EXT/job/Remote---Nova-Scotia/"
            "Sr-Director/apply/applyManually"
        )

    def title(self):
        return self._title

    def locator(self, sel):
        page = self

        class _Loc:
            def __init__(self):
                self._n = 0
                s = sel or ""
                if "signInSubmit" in s and page._sign_in:
                    self._n = 1
                if page._app and any(
                    x in s
                    for x in (
                        "legalNameSection",
                        "formField-name",
                        "file-upload",
                        "type='file'",
                        "applyManually",
                        "adventureButton",
                        "createAccountSubmit",
                        "verifyPassword",
                    )
                ):
                    self._n = 1

            def count(self):
                return self._n

            def is_visible(self):
                return self._n > 0

            @property
            def first(self):
                return self

        return _Loc()


assert_true(
    workday_stuck_on_sign_in(_SignInPage("Sign In - Gartner")),
    "Gartner Sign In title on applyManually is a login wall",
)
assert_true(
    not workday_stuck_on_sign_in(_SignInPage("My Information", sign_in=False, app_fields=True)),
    "application form is not a Sign In wall",
)
assert_true(
    not workday_stuck_on_sign_in(_SignInPage("Create Account/Sign In", sign_in=True, app_fields=True)),
    "Create Account with verifyPassword is completable",
)
assert_true(
    bool(ALREADY_APPLIED_RE.search("You have already applied to this job.")),
    "already-applied banner is skipped not walled",
)
assert_true(
    bool(ALREADY_APPLIED_RE.search("You are currently submitted to this job.")),
    "iCIMS currently-submitted is already applied",
)
assert_true(
    bool(SUBMITTED_RE.search("Your application was submitted successfully. Thank you for applying.")),
    "iCIMS success banner counts as submitted",
)
assert_true(
    workday_compliant_password("GoodPass123!") == "GoodPass123!",
    "already-compliant password is unchanged",
)
_weak = workday_compliant_password("short")
assert_true(len(_weak) >= 12, "compliant password is 12+")
assert_true(bool(re.search(r"[A-Z]", _weak)), "compliant password has uppercase")
assert_true(bool(re.search(r"[0-9]", _weak)), "compliant password has digit")
assert_true(bool(re.search(r"[^A-Za-z0-9]", _weak)), "compliant password has special")
assert_true(
    workday_compliant_password("short") == workday_compliant_password("short"),
    "compliant password is deterministic",
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

class _FakeFrame:
    def __init__(self, url: str, body: str = ""):
        self.url = url
        self._body = body

    def inner_text(self, sel: str = "body"):
        return self._body

    def locator(self, sel: str):
        page = self

        class _Body:
            def inner_text(self, *a, **k):
                return page._body

        if sel == "body":
            return _Body()
        return _Body()


class _FakeIframesPage:
    def __init__(self, url: str, frames: list):
        self.url = url
        self.frames = frames

    def locator(self, sel: str):
        class _Empty:
            def inner_text(self, *a, **k):
                return ""

            def count(self):
                return 0

        return _Empty()


assert_true(
    icims_hcaptcha_login(
        _FakeIframesPage(
            "https://careers-hyland.icims.com/jobs/13991/senior-software-architect---.net/job",
            [
                _FakeFrame(
                    "https://careers-hyland.icims.com/jobs/13991/senior-software-architect---.net/login?in_iframe=1",
                    "Enter Your Information\nEmail\nI accept\nProtected by hCaptcha",
                )
            ],
        )
    ),
    "iCIMS GDPR login + hCaptcha is a captcha wall",
)
assert_true(
    not icims_hcaptcha_login(
        _FakeIframesPage(
            "https://careers-hyland.icims.com/jobs/13991/senior-software-architect---.net/job",
            [
                _FakeFrame(
                    "https://careers-hyland.icims.com/jobs/13991/senior-software-architect---.net/job?in_iframe=1",
                    "Apply for this job online\nHyderabad, India",
                )
            ],
        )
    ),
    "iCIMS JD iframe is not a login wall",
)
assert_true(is_hard_ats_wall("CAPTCHA/bot wall"), "iCIMS hCaptcha must trip company wall cap")
assert_true(
    is_hard_ats_wall("captcha_solver_key_missing"),
    "legacy missing-key reason still trips company wall cap",
)
assert_true(
    is_hard_ats_wall("captcha_needs_owner_or_solver"),
    "no paid key + no headed wait trips company wall cap",
)
assert_true(
    is_hard_ats_wall("owner_captcha_unsolved"),
    "headed owner-wait miss trips company wall cap",
)
_logged_q = _FakeIframesPage(
    "https://careers-hyland.icims.com/jobs/14169/senior-software-architect/questions",
    [
        _FakeFrame(
            "https://careers-hyland.icims.com/jobs/14169/senior-software-architect/questions?in_iframe=1",
            "Mohammed Abdul Rafi Ahmed\nDashboard | Log Out\nCandidate Questions\nAre you willing to relocate?",
        )
    ],
)
assert_true(icims_logged_in(_logged_q), "Log Out on questions is logged in")
assert_true(not icims_should_wait_captcha(_logged_q), "logged-in questions skip captcha wait")
assert_true(callable(complete_icims), "complete_icims is wired")


# Footer "Protected by hCaptcha" alone is not a challenge wall.
class _FooterCaptchaPage:
    url = "https://example.com/apply"
    frames = []
    def locator(self, sel):
        class _Empty:
            def count(self):
                return 0
        return _Empty()
    def evaluate(self, *a, **k):
        return ""
assert_true(not visible_captcha_challenge(_FooterCaptchaPage()), "footer hCaptcha text must not block")

class _CandPage:
    url = "https://global-external-amd.icims.com/jobs/80159/x/candidate"
    frames = []
    def locator(self, sel):
        class _Empty:
            def count(self):
                return 0
        return _Empty()
assert_true(apply_form_still_open(_CandPage()), "candidate profile must count as open form")

print("tools/ats/test_complete.py OK")
