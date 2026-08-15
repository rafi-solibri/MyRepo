#!/usr/bin/env python3
"""Complete company-website / ATS applications (Workday, Greenhouse, generic).

Used by LinkedIn, Hitech City, Indeed, and any Playwright page that lands on
an employer ATS. Never invents success — confirmation text only.
"""

from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from tools.resume_paths import resume_upload_path
except Exception:  # pragma: no cover
    def resume_upload_path():
        for c in (
            "/workspace/resumes/Rafi_Resume.docx",
            "/home/ubuntu/resumes/Rafi_Resume.docx",
            "/home/ubuntu/Documents/Rafi_Resume.docx",
        ):
            if Path(c).is_file():
                return c
        raise FileNotFoundError("Rafi_Resume.docx missing")


PROFILE = {
    "first": "Mohammed Abdul Rafi",
    "last": "Ahmed",
    "full": "Mohammed Abdul Rafi Ahmed",
    "email": "",
    "phone": "8790251698",
    "linkedin": "https://linkedin.com/in/rafi-ahmed-mohammed-abdul-151644ba",
    "city": "Hyderabad",
    "state": "Telangana",
    "country": "India",
    "postal": "500032",
    "current_ctc": "5200000",
    "expected_ctc": "6500000",
    "notice": "0",
    "experience_years": "15",
    "school": "Acharya Nagarjuna University",
}

SUBMITTED_RE = re.compile(
    r"application (has been )?submitted|thank you for (your )?appl|"
    r"we (have )?received your (application|appl)|application received|"
    r"successfully (applied|submitted)|your application was sent|"
    r"application complete|you have successfully applied",
    re.I,
)

SSO_HOST_RE = re.compile(
    r"b2clogin\.com|login\.microsoftonline|accounts\.google\.com|okta\.com|"
    r"auth0\.com|passport\.amazon\.jobs|secure\.indeed\.com/(?:auth|account)|"
    r"signin\.aws|login\.microsoft",
    re.I,
)

WORKDAY_HOST_RE = re.compile(
    r"myworkdayjobs\.com|myworkdaysite\.com|workdayjobs|wd\d*\.myworkday",
    re.I,
)

GREENHOUSE_HOST_RE = re.compile(
    r"greenhouse\.io|job-boards\.greenhouse|smartrecruiters\.com|lever\.co|ashbyhq\.com",
    re.I,
)

CAPTCHA_CHALLENGE_HOSTS = (
    "hcaptcha.com",
    "challenges.cloudflare.com",
    "funcaptcha",
    "captcha-delivery.com",
    "datadome.co",
)

DEFAULT_TIME_CAP_S = int(os.environ.get("ATS_TIME_CAP_S", "390"))


def ats_email() -> str:
    for key in ("APPLY_EMAIL", "NAUKRI_APPLY_EMAIL", "LINKEDIN_EMAIL"):
        val = (os.environ.get(key) or "").strip()
        if val and "@" in val:
            return val
    return (PROFILE.get("email") or "").strip()


def ats_password() -> str:
    for key in (
        "WORKDAY_PASSWORD",
        "ATS_PASSWORD",
        "NAUKRI_WORKDAY_PASSWORD",
        "NAUKRI_ATS_PASSWORD",
    ):
        val = (os.environ.get(key) or "").strip()
        if val:
            return val
    return ""


def is_submitted_text(text: str | None) -> bool:
    return bool(SUBMITTED_RE.search(text or ""))


def classify_ats_host(url: str | None) -> str:
    u = url or ""
    if WORKDAY_HOST_RE.search(u):
        return "workday"
    if GREENHOUSE_HOST_RE.search(u):
        return "greenhouse"
    if SSO_HOST_RE.search(u):
        return "sso"
    if re.search(r"linkedin\.com", u, re.I):
        return "linkedin"
    return "generic"


def frame_url_is_captcha_challenge(url: str | None) -> bool:
    u = (url or "").lower()
    if any(x in u for x in CAPTCHA_CHALLENGE_HOSTS):
        return True
    if "recaptcha" in u and ("/bframe" in u or "challenge" in u):
        return True
    return False


def iframe_box_is_onscreen(box: dict | None) -> bool:
    if not box:
        return False
    return float(box.get("width") or 0) >= 20 and float(box.get("height") or 0) >= 20


def auth_wall_reason(
    url: str | None,
    text: str | None,
    *,
    has_password: bool = False,
    has_file: bool = False,
    has_workday_apply: bool = False,
    has_email_field: bool = False,
) -> str | None:
    """Return a wall reason, or None when guest/Workday apply can continue."""
    host = classify_ats_host(url)
    if host == "sso":
        return "ats_login_wall"
    blob = f"{url or ''}\n{text or ''}"
    if re.search(
        r"no longer accepting applications|this position has been filled|"
        r"job is no longer available|requisition is closed",
        blob,
        re.I,
    ):
        return "job_closed"
    if host == "workday" or has_workday_apply:
        # Workday Create Account / Sign In is completable when we have a password
        # and an email field — do NOT treat it as a hard wall.
        if has_workday_apply or has_file or (has_email_field and ats_password()):
            return None
        if has_password and not has_file and not has_email_field:
            return "ats_login_wall"
        return None
    if has_file:
        return None
    if has_password and re.search(
        r"sign in to (continue|apply)|log in to apply|create an account|"
        r"sign in using (microsoft|google)|employees must sign in",
        text or "",
        re.I,
    ):
        return "ats_login_wall"
    return None


def _body(page, limit: int = 4500) -> str:
    try:
        return (page.locator("body").inner_text(timeout=4000) or "")[:limit]
    except Exception:
        return ""


def _sleep(seconds: float) -> None:
    time.sleep(seconds)


def looks_submitted(page) -> bool:
    return is_submitted_text(_body(page, 7000))


def visible_captcha_challenge(page) -> bool:
    try:
        for fr in getattr(page, "frames", []) or []:
            if frame_url_is_captcha_challenge(getattr(fr, "url", None)):
                return True
        for sel in (
            "iframe[src*='recaptcha/bframe']",
            "iframe[src*='hcaptcha.com']",
            "iframe[src*='challenges.cloudflare.com']",
            "iframe[src*='captcha-delivery.com']",
        ):
            loc = page.locator(sel)
            n = min(loc.count(), 6)
            for i in range(n):
                el = loc.nth(i)
                try:
                    box = el.bounding_box()
                except Exception:
                    box = None
                if iframe_box_is_onscreen(box):
                    return True
    except Exception:
        return False
    return bool(re.search(r"verify you are human|press and hold|i'?m not a robot", _body(page, 1500), re.I))


def page_flags(page) -> dict:
    url = getattr(page, "url", "") or ""
    text = _body(page, 2500)
    has_password = False
    has_file = False
    has_email = False
    has_wd = False
    try:
        has_password = page.locator("input[type='password']").count() > 0
        has_file = page.locator("input[type='file']").count() > 0
        has_email = (
            page.locator("[data-automation-id='email'], input[type='email']").count() > 0
        )
        has_wd = bool(
            page.locator("[data-automation-id]").count()
            or re.search(r"Autofill with Resume|Apply Manually", text, re.I)
        )
    except Exception:
        pass
    return {
        "url": url,
        "text": text,
        "has_password": has_password,
        "has_file": has_file,
        "has_email": has_email,
        "has_wd": has_wd,
    }


def blocked_wall(page) -> str | None:
    if visible_captcha_challenge(page):
        return "CAPTCHA/bot wall"
    flags = page_flags(page)
    return auth_wall_reason(
        flags["url"],
        flags["text"],
        has_password=flags["has_password"],
        has_file=flags["has_file"],
        has_workday_apply=flags["has_wd"],
        has_email_field=flags["has_email"],
    )


def upload_resume(page) -> bool:
    path = resume_upload_path()
    uploaded = False
    for sel in ("input[type='file']", "input[accept*='pdf']", "input[accept*='doc']"):
        try:
            inputs = page.locator(sel)
            for i in range(min(inputs.count(), 4)):
                try:
                    inputs.nth(i).set_input_files(path, timeout=8000)
                    uploaded = True
                    _sleep(0.6)
                except Exception:
                    continue
        except Exception:
            continue
    return uploaded


def _click_text(page, labels: tuple[str, ...]) -> bool:
    for name in labels:
        try:
            btn = page.get_by_role("button", name=re.compile(rf"{re.escape(name)}", re.I))
            for i in range(min(btn.count(), 3)):
                b = btn.nth(i)
                if b.is_visible() and b.is_enabled():
                    try:
                        b.click(timeout=3000, force=True)
                    except Exception:
                        b.evaluate("el => el.click()")
                    _sleep(1.2)
                    return True
        except Exception:
            continue
        try:
            link = page.get_by_role("link", name=re.compile(rf"{re.escape(name)}", re.I))
            if link.count() and link.first.is_visible():
                link.first.click(timeout=3000)
                _sleep(1.2)
                return True
        except Exception:
            continue
        try:
            loc = page.get_by_text(name, exact=False).first
            if loc.is_visible():
                loc.click(timeout=2500, force=True)
                _sleep(1.2)
                return True
        except Exception:
            continue
    return False


def dismiss_cookies(page) -> None:
    _click_text(
        page,
        ("Accept All Cookies", "Accept Cookies", "Accept all", "Accept"),
    )
    for sel in (
        "[data-automation-id='legalNoticeAcceptButton']",
        "button[id*='cookie' i]",
    ):
        try:
            el = page.locator(sel).first
            if el.count() and el.is_visible():
                el.click(force=True)
                _sleep(0.3)
        except Exception:
            continue


def fill_labeled_fields(page) -> None:
    email = ats_email()
    pairs = [
        (r"first name|given name", PROFILE["first"]),
        (r"last name|surname|family name", PROFILE["last"]),
        (r"^full name$|legal name|your name", PROFILE["full"]),
        (r"email|e-mail", email),
        (r"phone|mobile|tel", PROFILE["phone"]),
        (r"linkedin|profile url", PROFILE["linkedin"]),
        (r"city|current city", PROFILE["city"]),
        (r"state|province|region", PROFILE["state"]),
        (r"country", PROFILE["country"]),
        (r"postal|zip", PROFILE["postal"]),
        (r"current (ctc|salary|compensation)|present ctc", PROFILE["current_ctc"]),
        (r"expected (ctc|salary|compensation)|desired salary", PROFILE["expected_ctc"]),
        (r"notice", PROFILE["notice"]),
        (r"years of experience|total experience", PROFILE["experience_years"]),
    ]
    try:
        labels = page.locator("label, [data-automation-id], .form-group label")
        n = min(labels.count(), 70)
    except Exception:
        return
    for i in range(n):
        lab = labels.nth(i)
        try:
            text = (lab.inner_text(timeout=350) or "").strip().lower()
        except Exception:
            continue
        if not text or len(text) > 90:
            continue
        for pat, val in pairs:
            if not re.search(pat, text, re.I):
                continue
            try:
                for_id = lab.get_attribute("for")
                ctrl = (
                    page.locator(f'[id="{for_id}"]').first
                    if for_id
                    else lab.locator(
                        "xpath=following::*[self::input or self::textarea or self::select][1]"
                    ).first
                )
                if not ctrl.count():
                    continue
                tag = ctrl.evaluate("e => e.tagName.toLowerCase()")
                if tag == "select":
                    try:
                        ctrl.select_option(label=re.compile(re.escape(val), re.I))
                    except Exception:
                        pass
                else:
                    ctrl.fill(val)
            except Exception:
                pass
            break


def fill_yes_no(page) -> None:
    pairs = [
        (r"authorized to work|legally authori[sz]ed", r"^Yes$"),
        (r"require sponsorship|visa sponsorship", r"^No$"),
        (r"previously (worked|employed)|former employee", r"^No$"),
        (r"relatives? (employed|work)", r"^No$"),
        (r"at least 18", r"^Yes$"),
        (r"willing to relocate", r"^Yes$"),
    ]
    for q_re, a_re in pairs:
        try:
            block = page.locator("fieldset, div, li, section").filter(has_text=re.compile(q_re, re.I)).first
            if not block.count() or not block.is_visible():
                continue
            ans = block.get_by_text(re.compile(a_re, re.I)).first
            if ans.count() and ans.is_visible():
                ans.click(force=True)
                _sleep(0.2)
        except Exception:
            continue


def tick_consents(page) -> None:
    for sel in (
        "input[type='checkbox'][name*='consent' i]",
        "input[type='checkbox'][id*='consent' i]",
        "input[type='checkbox'][name*='terms' i]",
        "[data-automation-id='createAccountCheckbox']",
    ):
        try:
            boxes = page.locator(sel)
            for i in range(min(boxes.count(), 4)):
                b = boxes.nth(i)
                if b.is_visible() and not b.is_checked():
                    b.check(force=True)
        except Exception:
            continue
    try:
        label = page.locator("label").filter(
            has_text=re.compile(r"I have (reviewed|read).{0,40}consent|I agree|I acknowledge", re.I)
        ).first
        if label.count() and label.is_visible():
            label.click(force=True)
    except Exception:
        pass


def click_advance(page) -> bool:
    for sel in (
        "[data-automation-id='pageFooterNextButton']",
        "button[data-automation-id='bottom-navigation-next-button']",
        "[data-automation-id='createAccountSubmitButton']",
        "[data-automation-id='signInSubmitButton']",
        "button[type='submit']",
        "input[type='submit']",
    ):
        try:
            el = page.locator(sel).first
            if el.count() and el.is_visible() and el.is_enabled():
                label = ((el.inner_text() or "") + " " + (el.get_attribute("aria-label") or "")).lower()
                if re.search(r"sign in with (google|microsoft|linkedin|apple)", label):
                    continue
                el.click(timeout=3000, force=True)
                _sleep(1.6)
                return True
        except Exception:
            continue
    return _click_text(
        page,
        (
            "Submit application",
            "Submit Application",
            "Send application",
            "Save and Continue",
            "Create Account",
            "Submit",
            "Continue",
            "Next",
            "Apply Manually",
            "Apply",
        ),
    )


def _type_automation(page, automation_id: str, value: str) -> bool:
    try:
        el = page.locator(
            f"[data-automation-id='{automation_id}'] input, [data-automation-id='{automation_id}']"
        ).first
        if not el.count() or not el.is_visible():
            return False
        el.click(force=True)
        el.fill("")
        el.fill(value)
        return True
    except Exception:
        return False


def workday_open_apply(page) -> None:
    dismiss_cookies(page)
    for sel in (
        "a[data-automation-id='adventureButton']",
        "button[data-automation-id='adventureButton']",
    ):
        try:
            el = page.locator(sel).first
            if el.count() and el.is_visible():
                el.click()
                _sleep(1.4)
                break
        except Exception:
            continue
    else:
        _click_text(page, ("Apply",))
    autofill = page.get_by_text("Autofill with Resume", exact=False).first
    manual = page.get_by_text("Apply Manually", exact=False).first
    try:
        if autofill.count() and autofill.is_visible():
            autofill.click(force=True)
            _sleep(1.8)
    except Exception:
        pass
    try:
        still = autofill.count() and autofill.is_visible()
        if (still or not autofill.count()) and manual.count() and manual.is_visible():
            manual.click(force=True)
            _sleep(1.6)
    except Exception:
        pass
    dismiss_cookies(page)


def workday_auth(page) -> str | None:
    """Create account or sign in. None = continue; string = hard wall."""
    password = ats_password()
    email = ats_email()
    if not email or "@" not in email:
        return "ats_email_missing"
    try:
        email_el = page.locator("[data-automation-id='email']").first
        if not (email_el.count() and email_el.is_visible()):
            _click_text(page, ("Sign in with email", "Use email", "Continue with email"))
            create = page.locator(
                "[data-automation-id='createAccountLink'], button:has-text('Create Account'), a:has-text('Create Account')"
            ).first
            if create.count() and create.is_visible():
                create.click(force=True)
                _sleep(1.2)
    except Exception:
        pass
    try:
        email_ready = page.locator("[data-automation-id='email']").first
        if not (email_ready.count() and email_ready.is_visible()):
            return None
    except Exception:
        return None
    if not password:
        return "ats_password_missing"
    verify = page.locator("[data-automation-id='verifyPassword']").first
    try:
        if not (verify.count() and verify.is_visible()):
            create = page.locator("[data-automation-id='createAccountLink']").first
            if create.count() and create.is_visible():
                create.click(force=True)
                _sleep(1.2)
    except Exception:
        pass
    _type_automation(page, "email", email)
    _type_automation(page, "password", password)
    try:
        if page.locator("[data-automation-id='verifyPassword']").first.is_visible():
            _type_automation(page, "verifyPassword", password)
            tick_consents(page)
            submit = page.locator(
                "[data-automation-id='createAccountSubmitButton'], button:has-text('Create Account')"
            ).first
            if submit.count() and submit.is_visible():
                submit.click(force=True)
                _sleep(2.8)
        else:
            submit = page.locator(
                "[data-automation-id='signInSubmitButton'], button:has-text('Sign In')"
            ).first
            if submit.count() and submit.is_visible():
                submit.click(force=True)
                _sleep(2.8)
    except Exception:
        pass
    text = _body(page, 2000)
    if re.search(r"already have an account|already exists|sign in instead", text, re.I):
        _click_text(page, ("Sign In",))
        _type_automation(page, "email", email)
        _type_automation(page, "password", password)
        _click_text(page, ("Sign In",))
        _sleep(2.0)
    if re.search(
        r"wrong email address or password|incorrect email or password|invalid email or password",
        _body(page, 1500),
        re.I,
    ):
        return "ats_login_wall"
    return None


def workday_fill_core(page) -> None:
    _type_automation(page, "legalNameSection_firstName", PROFILE["first"])
    _type_automation(page, "legalNameSection_lastName", PROFILE["last"])
    _type_automation(page, "formField-legalName--firstName", PROFILE["first"])
    _type_automation(page, "formField-legalName--lastName", PROFILE["last"])
    _type_automation(page, "addressSection_city", PROFILE["city"])
    _type_automation(page, "formField-city", PROFILE["city"])
    _type_automation(page, "formField-postalCode", PROFILE["postal"])
    _type_automation(page, "formField-phoneNumber", PROFILE["phone"])
    fill_labeled_fields(page)
    fill_yes_no(page)
    tick_consents(page)


def complete_workday(page, time_cap_s: int) -> tuple[str, str]:
    start = time.time()
    workday_open_apply(page)
    if looks_submitted(page):
        return "applied", "confirmation"
    auth = workday_auth(page)
    if auth:
        return "blocked", auth
    stuck = 0
    while time.time() - start < time_cap_s and stuck < 6:
        if looks_submitted(page):
            return "applied", "confirmation"
        wall = blocked_wall(page)
        if wall == "CAPTCHA/bot wall":
            return "blocked", wall
        if wall == "job_closed":
            return "skipped", wall
        text = _body(page, 2000)
        if re.search(r"^\s*Loading\b", text, re.I) and not re.search(r"First Name|My Information", text, re.I):
            _sleep(2.0)
            continue
        try:
            if not re.search(r"successfully uploaded|Rafi_Resume", text, re.I):
                upload_resume(page)
        except Exception:
            pass
        workday_fill_core(page)
        if click_advance(page):
            stuck = 0
            _sleep(1.8)
            continue
        if looks_submitted(page):
            return "applied", "confirmation"
        if re.search(r"Errors Found|is required and must have a value", _body(page, 1500), re.I):
            stuck += 1
            _sleep(0.8)
            continue
        stuck += 1
        _sleep(1.2)
    if looks_submitted(page):
        return "applied", "confirmation"
    return "blocked", "external_incomplete_or_timeout"


def complete_generic(page, time_cap_s: int) -> tuple[str, str]:
    start = time.time()
    stuck = 0
    while time.time() - start < time_cap_s and stuck < 5:
        if looks_submitted(page):
            return "applied", "confirmation"
        wall = blocked_wall(page)
        if wall == "CAPTCHA/bot wall":
            return "blocked", wall
        if wall == "job_closed":
            return "skipped", wall
        if wall == "ats_login_wall":
            guest = page.get_by_text(re.compile(r"Continue as guest|Apply without|Don't have an account", re.I)).first
            try:
                if guest.count() and guest.is_visible():
                    guest.click()
                    _sleep(1.0)
                else:
                    return "blocked", wall
            except Exception:
                return "blocked", wall
        try:
            upload_resume(page)
        except Exception:
            pass
        fill_labeled_fields(page)
        fill_yes_no(page)
        tick_consents(page)
        if click_advance(page):
            stuck = 0
            _sleep(1.4)
            continue
        stuck += 1
        _sleep(1.0)
    if looks_submitted(page):
        return "applied", "confirmation"
    return "blocked", "external_incomplete_or_timeout"


def complete_ats(page, time_cap_s: int | None = None) -> tuple[str, str]:
    """Fill + submit the current ATS page. Returns (status, reason)."""
    cap = int(time_cap_s or DEFAULT_TIME_CAP_S)
    if looks_submitted(page):
        return "applied", "confirmation"
    if visible_captcha_challenge(page):
        return "blocked", "CAPTCHA/bot wall"
    flags = page_flags(page)
    host = classify_ats_host(flags["url"])
    if host == "sso":
        return "blocked", "ats_login_wall"
    if host == "linkedin":
        return "blocked", "did_not_leave_linkedin"
    wall = auth_wall_reason(
        flags["url"],
        flags["text"],
        has_password=flags["has_password"],
        has_file=flags["has_file"],
        has_workday_apply=flags["has_wd"],
        has_email_field=flags["has_email"],
    )
    if wall == "job_closed":
        return "skipped", wall
    if wall and host != "workday" and not flags["has_wd"]:
        return "blocked", wall
    if host == "workday" or flags["has_wd"]:
        return complete_workday(page, cap)
    return complete_generic(page, cap)


def complete_ats_url(url: str, time_cap_s: int | None = None, cdp: str | None = None) -> tuple[str, str, str]:
    """Open an ATS URL in Playwright and complete it. Returns (status, reason, final_url)."""
    from playwright.sync_api import sync_playwright

    cap = int(time_cap_s or DEFAULT_TIME_CAP_S)
    cdp_url = cdp or os.environ.get("ATS_CDP") or os.environ.get("LINKEDIN_CDP") or "http://127.0.0.1:9222"
    with sync_playwright() as p:
        owned = False
        browser = None
        try:
            browser = p.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.new_page()
        except Exception:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            owned = True
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            _sleep(1.5)
            status, reason = complete_ats(page, time_cap_s=cap)
            return status, reason, page.url or url
        finally:
            try:
                if not owned:
                    page.close()
            except Exception:
                pass
            if owned and browser is not None:
                browser.close()


def host_label(url: str | None) -> str:
    try:
        return urlparse(url or "").netloc or "unknown"
    except Exception:
        return "unknown"
