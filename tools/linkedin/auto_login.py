#!/usr/bin/env python3
"""Unattended LinkedIn CDP login recovery for daily cron.

Tries, in order:
1. Already signed in (feed + li_at, not login/checkpoint)
2. Continue with Google (GSI) using Google cookies already in the CDP profile
3. Email/password from LINKEDIN_EMAIL + LINKEDIN_PASSWORD secrets

On success, exits 0. On CAPTCHA/checkpoint that needs a human, exits 6.
On missing credentials / other failure, exits 5.

Usage:
  python3 tools/linkedin/auto_login.py
  LINKEDIN_CDP=http://127.0.0.1:9222 python3 tools/linkedin/auto_login.py
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

CDP = os.environ.get("LINKEDIN_CDP", "http://127.0.0.1:9222")
EMAIL = (
    os.environ.get("LINKEDIN_EMAIL")
    or os.environ.get("LINKEDIN_USER")
    or os.environ.get("LINKEDIN_USERNAME")
    or ""
).strip()
PASSWORD = (os.environ.get("LINKEDIN_PASSWORD") or "").strip()
DEFAULT_EMAIL = "rafi.success@gmail.com"
TIMEOUT_S = int(os.environ.get("LINKEDIN_AUTO_LOGIN_TIMEOUT_S", "120"))


def _art() -> Path:
    cloud = Path("/opt/cursor/artifacts")
    if cloud.is_dir():
        return cloud
    d = Path(__file__).resolve().parents[2] / "artifacts"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _cookies_has_li_at(ctx) -> bool:
    try:
        return any(c.get("name") == "li_at" for c in ctx.cookies(["https://www.linkedin.com"]))
    except Exception:
        return False


def _url_loginish(url: str) -> bool:
    return bool(re.search(r"/login|authwall|/checkpoint|challenge|uas/login", (url or "").lower()))


def _close_stale_auth_tabs(ctx) -> None:
    """Close leftover challenge/Google chooser tabs, but never the last tab."""
    pages = list(ctx.pages or [])
    if len(pages) <= 1:
        return
    for p in pages:
        if len(list(ctx.pages or [])) <= 1:
            break
        u = p.url or ""
        if re.search(r"checkpoint|challenge|accounts\.google\.com/gsi/select", u, re.I):
            try:
                p.close()
            except Exception:
                pass


def _is_signed_in(ctx, page) -> bool:
    if not _cookies_has_li_at(ctx):
        return False
    # Prefer verifying via feed navigation; leftover challenge tabs are OK if li_at works.
    try:
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=60000)
        time.sleep(1.5)
    except Exception:
        pass
    url = page.url or ""
    if _url_loginish(url):
        return False
    try:
        body = page.locator("body").inner_text()[:2000]
    except Exception:
        body = ""
    if re.search(r"Start a post|My Network|Notifications", body, re.I):
        _close_stale_auth_tabs(ctx)
        return True
    return "/feed" in url.lower() or "/jobs" in url.lower()


def _on_captcha(page) -> bool:
    url = (page.url or "").lower()
    if "/checkpoint" in url or "challenge" in url:
        return True
    try:
        body = page.locator("body").inner_text()[:1500]
    except Exception:
        body = ""
    if re.search(r"quick security check|not a robot|captcha|security verification", body, re.I):
        return True
    try:
        if page.locator(
            "iframe[src*='recaptcha'], iframe#captcha-internal, iframe[src*='protechts']"
        ).count():
            return True
    except Exception:
        pass
    return False


def _pick_linkedin_page(ctx):
    pages = list(ctx.pages or [])
    for p in pages:
        if re.search(r"/feed|/jobs|/in/", p.url or "", re.I):
            return p
    for p in pages:
        if "linkedin.com" in (p.url or "") and not re.search(
            r"checkpoint|challenge", p.url or "", re.I
        ):
            return p
    for p in pages:
        if "linkedin.com" in (p.url or ""):
            return p
    if pages:
        return pages[0]
    try:
        return ctx.new_page()
    except Exception:
        # Browser may refuse new tabs mid-challenge — reuse any open page.
        pages = list(ctx.pages or [])
        if pages:
            return pages[0]
        raise


def _click_continue_google(ctx, page) -> bool:
    """Click LinkedIn Continue with Google and choose the remembered Google account."""
    frames = [f for f in page.frames if "accounts.google.com/gsi/button" in (f.url or "")]
    popup = None
    clicked = False

    def _do_click():
        nonlocal clicked
        if frames:
            try:
                frames[0].locator("div[role=button]").first.click(force=True, timeout=8000)
                clicked = True
                return
            except Exception:
                pass
        btn = page.locator("[role=button]:has-text('Continue with Google')")
        if btn.count():
            btn.first.click(force=True, timeout=8000)
            clicked = True

    try:
        with ctx.expect_page(timeout=15000) as np:
            _do_click()
        if clicked:
            popup = np.value
    except Exception:
        if not clicked:
            try:
                _do_click()
            except Exception:
                return False
        time.sleep(2)

    if not clicked:
        return False

    if popup is not None:
        try:
            popup.wait_for_load_state("domcontentloaded", timeout=30000)
        except Exception:
            pass
        time.sleep(1.5)
        # Account chooser: "Rafi … / rafi.success@gmail.com"
        chosen = False
        for sel in ("div[role='link']", "div[data-identifier]", "div[data-email]"):
            try:
                locs = popup.locator(sel)
                n = min(locs.count(), 8)
            except Exception:
                continue
            for i in range(n):
                try:
                    t = (locs.nth(i).inner_text() or "") + " " + (
                        locs.nth(i).get_attribute("data-identifier") or ""
                    )
                except Exception:
                    continue
                if re.search(r"rafi\.success@gmail\.com|@gmail\.com|Rafi Ahmed", t, re.I):
                    try:
                        locs.nth(i).click(timeout=8000)
                        chosen = True
                        time.sleep(2)
                        break
                    except Exception:
                        # Popup may auto-close after click
                        chosen = True
                        break
            if chosen:
                break
        if not chosen:
            # Single-account auto-select may already proceed; wait.
            time.sleep(2)
        for name in ("Continue", "Allow", "Next", "Confirm"):
            try:
                b = popup.get_by_role("button", name=re.compile(rf"^{name}$", re.I))
                if b.count():
                    b.first.click(timeout=5000)
                    time.sleep(1)
            except Exception:
                break
    return True


def _visible_locator(page, selectors: str):
    """Return first visible locator for comma-separated CSS selectors.

    LinkedIn login ships duplicate hidden email/password inputs with obfuscated
    ids; `.first` often hits a non-visible field and the Sign-in submit no-ops
    or trips challenge_global_internal_error.
    """
    for sel in [s.strip() for s in selectors.split(",") if s.strip()]:
        loc = page.locator(sel)
        try:
            n = min(loc.count(), 8)
        except Exception:
            continue
        for i in range(n):
            try:
                el = loc.nth(i)
                if el.is_visible():
                    return el
            except Exception:
                continue
    return None


def _password_login(page, email: str, password: str) -> bool:
    try:
        email_box = _visible_locator(
            page,
            "#username, input[name='session_key'], input[type='email'], input[autocomplete='username']",
        )
        pass_box = _visible_locator(
            page,
            "#password, input[name='session_password'], input[type='password'], input[autocomplete='current-password']",
        )
        if email_box is not None and email:
            try:
                cur = email_box.input_value()
            except Exception:
                cur = ""
            if not cur or "@" not in cur:
                email_box.fill(email)
        if pass_box is None:
            return False
        # pressSequentially avoids mangling special chars like '%' in passwords.
        try:
            pass_box.click(timeout=3000)
            pass_box.fill("")
            pass_box.press_sequentially(password, delay=25)
        except Exception:
            pass_box.fill(password)
        # Keep me signed in when shown (reduces next-day checkpoint rate).
        try:
            keep = _visible_locator(page, "input[type='checkbox']")
            if keep is not None and not keep.is_checked():
                keep.check(force=True)
        except Exception:
            pass
        btn = page.get_by_role("button", name=re.compile(r"^Sign in$", re.I))
        if btn.count() == 0:
            btn = page.locator("button[type='submit']")
        # Prefer a visible Sign in button.
        clicked = False
        try:
            n = min(btn.count(), 6)
            for i in range(n):
                if btn.nth(i).is_visible():
                    btn.nth(i).click(timeout=5000)
                    clicked = True
                    break
        except Exception:
            pass
        if not clicked:
            btn.first.click(timeout=5000)
        return True
    except Exception:
        return False


def _goto_login_clean(ctx, page):
    """Leave checkpoint/Google tabs and open a fresh /login form."""
    _close_stale_auth_tabs(ctx)
    page = _pick_linkedin_page(ctx)
    try:
        page.goto(
            "https://www.linkedin.com/uas/login",
            wait_until="domcontentloaded",
            timeout=60000,
        )
        time.sleep(1.5)
        # Prefer classic /login form when available.
        if "login" not in (page.url or "").lower() or "checkpoint" in (page.url or "").lower():
            page.goto(
                "https://www.linkedin.com/login",
                wait_until="domcontentloaded",
                timeout=60000,
            )
            time.sleep(2)
    except Exception:
        try:
            page.goto(
                "https://www.linkedin.com/login",
                wait_until="domcontentloaded",
                timeout=60000,
            )
            time.sleep(2)
        except Exception:
            pass
    return _pick_linkedin_page(ctx)


def _wait_signed_in(ctx, page, deadline: float, via: str, out: dict) -> int | None:
    """Poll until signed in / captcha / timeout. Returns exit code or None to continue."""
    while time.time() < deadline:
        page = _pick_linkedin_page(ctx)
        if _cookies_has_li_at(ctx) and _is_signed_in(ctx, page):
            out.update(ok=True, reason=via, url=page.url)
            print(json.dumps(out))
            return 0
        if _on_captcha(page) and not _cookies_has_li_at(ctx):
            out.update(ok=False, reason="captcha_checkpoint", url=page.url, via=via)
            try:
                page.screenshot(path=str(_art() / "linkedin-auto-login-captcha.png"), timeout=8000)
            except Exception:
                pass
            # Caller may still try another method — signal with return 6 only
            # when no further fallback exists.
            return 6
        time.sleep(2)
    out["attempts"].append({"step": via, "timed_out": True})
    return None


def main() -> int:
    out: dict = {"ok": False, "attempts": []}
    deadline = time.time() + TIMEOUT_S
    email = EMAIL or DEFAULT_EMAIL
    # Cloud datacenter IPs often CAPTCHA Google SSO; prefer password when set.
    prefer_password = bool(PASSWORD) and os.environ.get(
        "LINKEDIN_PREFER_PASSWORD", "1"
    ).strip() not in ("0", "false", "no")

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(CDP)
        except Exception as e:
            out.update(reason="cdp_connect_failed", error=str(e)[:200])
            print(json.dumps(out))
            return 4

        ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        page = _pick_linkedin_page(ctx)
        try:
            page.bring_to_front()
        except Exception:
            pass

        try:
            page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(2)
        except Exception as e:
            out["attempts"].append({"step": "goto_feed", "error": str(e)[:120]})

        if _is_signed_in(ctx, page):
            out.update(ok=True, reason="already_signed_in", url=page.url)
            print(json.dumps(out))
            return 0

        page = _goto_login_clean(ctx, page)

        def try_password() -> int | None:
            if not PASSWORD:
                out["attempts"].append(
                    {
                        "step": "password",
                        "skipped": True,
                        "hint": "Set Cursor secrets LINKEDIN_EMAIL + LINKEDIN_PASSWORD for password fallback",
                    }
                )
                return None
            nonlocal_page = _goto_login_clean(ctx, _pick_linkedin_page(ctx))
            out["attempts"].append({"step": "password", "email": email[:3] + "***"})
            if not _password_login(nonlocal_page, email, PASSWORD):
                out["attempts"].append({"step": "password", "submitted": False})
                return None
            return _wait_signed_in(ctx, nonlocal_page, deadline, "password", out)

        def try_google() -> int | None:
            nonlocal_page = _goto_login_clean(ctx, _pick_linkedin_page(ctx))
            out["attempts"].append({"step": "google_sso", "started": True})
            if not _click_continue_google(ctx, nonlocal_page):
                out["attempts"].append({"step": "google_sso", "clicked": False})
                return None
            return _wait_signed_in(ctx, nonlocal_page, deadline, "google_sso", out)

        order = ("password", "google_sso") if prefer_password else ("google_sso", "password")
        captcha_seen = False
        for step in order:
            rc = try_password() if step == "password" else try_google()
            if rc == 0:
                return 0
            if rc == 6:
                captcha_seen = True
                # Do not hard-stop — try the other method (password after SSO CAPTCHA).
                continue

        page = _pick_linkedin_page(ctx)
        if _cookies_has_li_at(ctx) and _is_signed_in(ctx, page):
            out.update(ok=True, reason="recovered", url=page.url)
            print(json.dumps(out))
            return 0
        if captcha_seen or (_on_captcha(page) and not _cookies_has_li_at(ctx)):
            out.update(ok=False, reason="captcha_checkpoint", url=page.url)
            print(json.dumps(out))
            return 6

        out.update(
            ok=False,
            reason="linkedin_login_required",
            url=page.url,
            has_li_at=_cookies_has_li_at(ctx),
            hint="CAPTCHA/checkpoint or Google SSO failed; set Cursor secret LINKEDIN_PASSWORD and re-run",
        )
        print(json.dumps(out))
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
