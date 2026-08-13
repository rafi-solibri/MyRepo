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


def looks_submitted(page: Page) -> bool:
    try:
        body = page.locator("body").inner_text()[:7000]
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


def blocked_wall(page: Page) -> str | None:
    # Frame/iframe CAPTCHA first — body text often omits "captcha" while reCAPTCHA blocks submit.
    # Do NOT treat bare [data-sitekey] as a wall (many ATS pages embed dormant sitekeys).
    try:
        for fr in page.frames:
            u = (fr.url or "").lower()
            if any(
                x in u
                for x in (
                    "/recaptcha/",
                    "recaptcha/enterprise",
                    "hcaptcha.com",
                    "challenges.cloudflare.com",
                    "geetest",
                    "funcaptcha",
                    "captcha-delivery.com",  # DataDome (SmartRecruiters / Experian)
                    "geo.captcha-delivery.com",
                    "datadome.co",
                )
            ):
                return "CAPTCHA/bot wall"
        # Visible challenge iframes only
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
            if loc.count() and loc.first.is_visible():
                return "CAPTCHA/bot wall"
    except Exception:
        pass
    try:
        body = page.locator("body").inner_text()[:4500]
    except Exception:
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
    if re.search(r"sign in to continue|log in to apply|create an account|sign in to apply", body, re.I):
        if page.locator("input[type='file'], input[type='email']").count() == 0:
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


def attempt_ats_apply(page: Page, time_cap_s: int = 180) -> tuple[str, str]:
    """Fill + submit current ATS page. Returns (status, reason)."""
    start = time.time()
    # Bail before expensive fill loops when CAPTCHA/login already present.
    wall = blocked_wall(page)
    if wall:
        status = "skipped" if wall == "job_closed" else "blocked"
        return status, wall
    if looks_submitted(page):
        return "applied", "confirmation"
    try:
        upload_resume(page)
    except Exception:
        pass
    if time.time() - start >= time_cap_s:
        return "blocked", "ats_time_cap"
    wall = blocked_wall(page)
    if wall:
        status = "skipped" if wall == "job_closed" else "blocked"
        return status, wall
    try:
        fill_common(page)
    except Exception:
        pass
    steps = 0
    while time.time() - start < time_cap_s and steps < 8:
        wall = blocked_wall(page)
        if wall:
            status = "skipped" if wall == "job_closed" else "blocked"
            return status, wall
        if looks_submitted(page):
            return "applied", "confirmation"
        if not try_submit(page):
            break
        try:
            upload_resume(page)
            fill_common(page)
        except Exception:
            pass
        steps += 1
        time.sleep(0.8)
    if looks_submitted(page):
        return "applied", "confirmation"
    if time.time() - start >= time_cap_s:
        return "blocked", "ats_time_cap"
    return "blocked", "ats_incomplete_or_stuck"
