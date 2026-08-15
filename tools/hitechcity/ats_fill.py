#!/usr/bin/env python3
"""Shared ATS form fill / submit helpers for company career portals."""

from __future__ import annotations

import re
import time
from pathlib import Path

from playwright.sync_api import Page

PROFILE = {
    "first": "Mohammed Abdul Rafi",
    "last": "Ahmed",
    "full": "Mohammed Abdul Rafi Ahmed",
    "phone": "8790251698",
    "email": "rafi.success@gmail.com",
    "linkedin": "https://linkedin.com/in/rafi-ahmed-mohammed-abdul-151644ba",
    "city": "Hyderabad",
    "state": "Telangana",
    "country": "India",
    "current_ctc": "5200000",
    "expected_ctc": "6500000",
    "current_ctc_lakhs": "52",
    "expected_ctc_lakhs": "65",
    "notice": "0",
    "experience_years": "15",
}


def resume_path() -> str:
    for c in [
        "/workspace/resumes/Rafi_Resume.docx",
        "/home/ubuntu/resumes/Rafi_Resume.docx",
        "/home/ubuntu/Documents/Rafi_Resume.docx",
        "/opt/cursor/artifacts/Rafi_Resume.docx",
    ]:
        if Path(c).is_file():
            return c
    raise FileNotFoundError("Rafi_Resume.docx missing")


# SmartRecruiters OneClick / Indeed OAuth / Google GSI — not guest-applyable.
AUTH_WALL_URL = re.compile(
    r"passport\.amazon\.jobs|login\.microsoftonline|accounts\.google\.com|"
    r"secure\.indeed\.com/(?:auth|account)|indeed\.com/auth|"
    r"okta\.com|login\.microsoft|signin\.aws|"
    r"/checkpoint/challenge|linkedin\.com/uas/login|"
    r"smartrecruiters\.com/[^/]+/login|"
    r"login\.cognizant|cognizant\.okta|talent\.cognizant\.com/[^?\s]*(?:login|login2)|"
    r"eightfold\.ai/(?:login|signin|auth)",
    re.I,
)


def auth_wall_url(url: str | None) -> bool:
    """True when the browser landed on a login/SSO/OAuth wall (fail fast)."""
    return bool(url and AUTH_WALL_URL.search(url))


def looks_workday_page(page: Page) -> bool:
    """Workday Create Account / Apply Manually is completable — not a login wall."""
    url = getattr(page, "url", "") or ""
    if re.search(r"myworkdayjobs|myworkdaysite|workdayjobs", url, re.I):
        return True
    try:
        for sel in (
            "[data-automation-id='createAccountSubmitButton']",
            "[data-automation-id='adventureButton']",
            "[data-automation-id='applyManually']",
            "[data-automation-id='signInSubmitButton']",
        ):
            if page.locator(sel).count():
                return True
    except Exception:
        pass
    return False


def _body_text(page: Page, limit: int = 4500) -> str:
    """inner_text with a hard timeout so SSO pages cannot hang careers forever."""
    try:
        return (page.locator("body").inner_text(timeout=4000) or "")[:limit]
    except Exception:
        return ""


def looks_submitted(page: Page) -> bool:
    try:
        body = _body_text(page, 7000)
    except Exception:
        return False
    return bool(
        re.search(
            r"application (has been )?submitted|thank you for (your )?appl|"
            r"we (have )?received your (application|appl)|application received|"
            r"successfully applied|your application was sent|application complete",
            body,
            re.I,
        )
    )


# DataDome / hCaptcha / CF / recaptcha *challenge* frames. Dormant recaptcha
# api2/anchor badges (0×0, visibility:hidden) are NOT walls — Microsoft/Qualcomm
# apply pages embed them next to a Sign-in form.
_CAPTCHA_CHALLENGE_HOSTS = (
    "hcaptcha.com",
    "challenges.cloudflare.com",
    "geetest",
    "funcaptcha",
    "captcha-delivery.com",  # DataDome (SmartRecruiters / Experian)
    "geo.captcha-delivery.com",
    "datadome.co",
)


def frame_url_is_captcha_challenge(url: str) -> bool:
    """True for bot-challenge frames, not hidden reCAPTCHA badges."""
    u = (url or "").lower()
    if any(x in u for x in _CAPTCHA_CHALLENGE_HOSTS):
        return True
    if "recaptcha" in u and ("/bframe" in u or "challenge" in u):
        return True
    return False


def iframe_looks_onscreen(el) -> bool:
    """reCAPTCHA checkbox/challenge is on-screen; 0×0 hidden badges are not."""
    try:
        if not el.is_visible():
            return False
        box = el.bounding_box()
        if not box:
            return False
        return float(box.get("width") or 0) >= 20 and float(box.get("height") or 0) >= 20
    except Exception:
        return False


def blocked_wall(page: Page) -> str | None:
    # URL-first: Indeed OAuth / Google SSO / passport walls must not burn ATS time caps.
    try:
        if auth_wall_url(getattr(page, "url", None) or ""):
            return "login/account wall"
        for fr in getattr(page, "frames", []) or []:
            if auth_wall_url(getattr(fr, "url", None) or ""):
                return "login/account wall"
    except Exception:
        pass
    # Frame/iframe CAPTCHA first — body text often omits "captcha" while a real
    # challenge blocks submit. Do NOT treat bare [data-sitekey] or hidden
    # recaptcha/api2/anchor badges as a wall (many ATS pages embed them).
    try:
        for fr in page.frames:
            if frame_url_is_captcha_challenge(fr.url or ""):
                return "CAPTCHA/bot wall"
        for sel in (
            "iframe[src*='recaptcha/']",
            "iframe[src*='hcaptcha.com']",
            "iframe[src*='captcha-delivery.com']",
            "iframe[src*='datadome']",
            "iframe[title*='reCAPTCHA']",
            "iframe[title*='captcha']",
            "iframe[title*='Verification']",
        ):
            loc = page.locator(sel)
            n = min(loc.count(), 8)
            for i in range(n):
                el = loc.nth(i)
                src = (el.get_attribute("src") or "").lower()
                title = (el.get_attribute("title") or "").lower()
                if frame_url_is_captcha_challenge(src) or "datadome" in src or "captcha-delivery" in src:
                    return "CAPTCHA/bot wall"
                if "recaptcha" in src or "captcha" in title or "verification" in title:
                    if iframe_looks_onscreen(el):
                        return "CAPTCHA/bot wall"
    except Exception:
        pass
    body = _body_text(page, 4500)
    if not body:
        return None
    if re.search(
        r"no longer accepting applications|this position has been filled|"
        r"job is no longer available|requisition is closed|no longer available",
        body,
        re.I,
    ):
        return "job_closed"
    if re.search(
        r"captcha|verify you are human|cloudflare|attention required|i'?m not a robot|"
        r"verification required|datadome|press and hold",
        body,
        re.I,
    ):
        return "CAPTCHA/bot wall"
    # Workday Create Account / Apply Manually is the apply form — complete it.
    if looks_workday_page(page):
        return None
    # Strong SSO chooser only. JD/nav chrome ("Create an account", "Sign in")
    # is on almost every career listing and must not block Apply.
    if re.search(
        r"select a method below to sign in|"
        r"if you are a microsoft employee|"
        r"employees must sign in|"
        r"current \w+ employees must sign in|"
        r"we don't recognize this email|"
        r"sign in\s*\|\s*indeed accounts|"
        r"continue with google|continue with indeed|"
        r"sign in using (microsoft|google|linkedin|facebook|apple)",
        body,
        re.I,
    ):
        try:
            has_resume = page.locator("input[type='file']").count() > 0
        except Exception:
            has_resume = False
        has_guest = bool(
            re.search(
                r"apply (now|manually|for this job|without)|autofill with resume|"
                r"i'?m interested|upload (your )?resume",
                body,
                re.I,
            )
        )
        if not has_resume and not has_guest:
            return "login/account wall"
    return None


def upload_resume(page: Page) -> bool:
    path = resume_path()
    uploaded = False
    for sel in ("input[type='file']", "input[accept*='pdf']", "input[accept*='doc']"):
        try:
            inputs = page.locator(sel)
            for i in range(min(inputs.count(), 4)):
                inp = inputs.nth(i)
                try:
                    inp.set_input_files(path, timeout=4000)
                    uploaded = True
                    time.sleep(0.8)
                except Exception:
                    continue
        except Exception:
            continue
    return uploaded


def fill_common(page: Page) -> None:
    pairs = [
        (r"first name|given name", PROFILE["first"]),
        (r"last name|surname|family name", PROFILE["last"]),
        (r"^full name$|legal name|your name", PROFILE["full"]),
        (r"email|e-mail", PROFILE["email"]),
        (r"phone|mobile|tel", PROFILE["phone"]),
        (r"linkedin|profile url", PROFILE["linkedin"]),
        (r"city|current city", PROFILE["city"]),
        (r"state|province|region", PROFILE["state"]),
        (r"country", PROFILE["country"]),
        (r"current (ctc|salary|compensation)|present ctc", PROFILE["current_ctc"]),
        (r"expected (ctc|salary|compensation)|desired salary", PROFILE["expected_ctc"]),
        (r"notice", PROFILE["notice"]),
        (r"years of experience|total experience", PROFILE["experience_years"]),
    ]
    labels = page.locator("label, [data-automation-id], .form-group label, .application-label")
    n = min(labels.count(), 60)
    for i in range(n):
        lab = labels.nth(i)
        try:
            text = (lab.inner_text(timeout=400) or "").strip().lower()
        except Exception:
            continue
        if not text or len(text) > 90:
            continue
        for pat, val in pairs:
            if re.search(pat, text, re.I):
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

    # Checkbox consent / work authorization defaults when obvious
    for sel in (
        "input[type='checkbox'][name*='consent']",
        "input[type='checkbox'][id*='consent']",
        "input[type='checkbox'][name*='terms']",
    ):
        try:
            boxes = page.locator(sel)
            for i in range(min(boxes.count(), 3)):
                b = boxes.nth(i)
                if b.is_visible() and not b.is_checked():
                    b.check(force=True)
        except Exception:
            pass


def try_click_named(page: Page, names: tuple[str, ...]) -> bool:
    for name in names:
        try:
            btn = page.get_by_role("button", name=re.compile(rf"{re.escape(name)}", re.I))
            for i in range(min(btn.count(), 3)):
                b = btn.nth(i)
                if b.is_visible() and b.is_enabled():
                    label = ((b.inner_text() or "") + " " + (b.get_attribute("aria-label") or "")).strip()
                    if re.search(r"apply", name, re.I) and re.search(
                        r"view applied|applied jobs|already applied", label, re.I
                    ):
                        continue
                    try:
                        b.click(timeout=3000, force=True)
                    except Exception:
                        b.evaluate("el => el.click()")
                    time.sleep(1.4)
                    return True
        except Exception:
            continue
        try:
            link = page.get_by_role("link", name=re.compile(rf"{re.escape(name)}", re.I))
            if link.count() and link.first.is_visible():
                link.first.click(timeout=3000)
                time.sleep(1.4)
                return True
        except Exception:
            continue
    return False


def try_submit(page: Page) -> bool:
    return try_click_named(
        page,
        (
            "Submit application",
            "Submit Application",
            "Submit",
            "Send application",
            "Apply",
            "Continue",
            "Next",
            "Save and Continue",
            "Review",
        ),
    )


def attempt_ats_apply(page: Page, time_cap_s: int = 390) -> tuple[str, str]:
    """Fill + submit current ATS page. Returns (status, reason)."""
    try:
        from tools.ats.complete import complete_ats
    except Exception:
        from ats.complete import complete_ats  # type: ignore
    return complete_ats(page, time_cap_s=time_cap_s)
