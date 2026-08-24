#!/usr/bin/env python3
"""Unattended LinkedIn CDP login recovery for daily cron.

Tries, in order:
1. Already signed in (feed + li_at, not login/checkpoint)
2. Continue with Google (GSI) using Google cookies already in the CDP profile
3. Email/password from LINKEDIN_EMAIL + LINKEDIN_PASSWORD secrets

On success, exits 0. On CAPTCHA/checkpoint that needs a human, exits 6.
On missing credentials / other failure, exits 5.
On temporary account restriction whose lift time is beyond the wait budget, exits 7.

Temporary restrictions (not interactive CAPTCHA) that lift within
LINKEDIN_RESTRICTION_WAIT_MAX_S are waited out and then re-tried.

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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from playwright.sync_api import sync_playwright

CDP = os.environ.get("LINKEDIN_CDP", "http://127.0.0.1:9222")
EMAIL = (
    os.environ.get("LINKEDIN_EMAIL")
    or os.environ.get("LINKEDIN_USER")
    or os.environ.get("LINKEDIN_USERNAME")
    or os.environ.get("GOOGLE_EMAIL")
    or ""
).strip()
PASSWORD = (os.environ.get("LINKEDIN_PASSWORD") or "").strip()
DEFAULT_EMAIL = "rafi.success@gmail.com"
TIMEOUT_S = int(os.environ.get("LINKEDIN_AUTO_LOGIN_TIMEOUT_S", "120"))
# Each method (GSI / each password candidate) gets its own wait — a shared
# deadline made password-after-SSO look like a generic timeout.
METHOD_TIMEOUT_S = int(os.environ.get("LINKEDIN_AUTO_LOGIN_METHOD_TIMEOUT_S", "90"))  # pragma: allowlist secret
# Wait out short temporary restrictions (cron can land mid-ban).
RESTRICTION_WAIT_MAX_S = int(os.environ.get("LINKEDIN_RESTRICTION_WAIT_MAX_S", "7200"))
RESTRICTION_BUFFER_S = int(os.environ.get("LINKEDIN_RESTRICTION_BUFFER_S", "90"))

# Cookie names can be present while Google/portal sessions are dead.
PASSWORD_ENV_KEYS = (
    "LINKEDIN_PASSWORD",  # pragma: allowlist secret
    "GOOGLE_PASSWORD",
    "NAUKRI_WORKDAY_PASSWORD",
    "ATS_PASSWORD",
    "WORKDAY_PASSWORD",
    "NAUKRI_ATS_PASSWORD",
)
WRONG_PASSWORD_RE = re.compile(
    r"that.?s not the right password|wrong password|incorrect password|"
    r"couldn.?t sign you in|enter a valid password",
    re.I,
)

_TZ_ALIASES = {
    "PDT": "America/Los_Angeles",
    "PST": "America/Los_Angeles",
    "EDT": "America/New_York",
    "EST": "America/New_York",
    "CDT": "America/Chicago",
    "CST": "America/Chicago",
    "MDT": "America/Denver",
    "MST": "America/Denver",
    "UTC": "UTC",
    "GMT": "UTC",
    "IST": "Asia/Kolkata",
}



def wrong_password_text(text: str) -> bool:
    """True when the portal or Google shows an explicit wrong-password error."""
    return bool(text and WRONG_PASSWORD_RE.search(text))


def password_candidates(env: dict | None = None) -> list[str]:
    """Unique non-empty passwords from owner secret aliases (values never logged)."""
    src = env if env is not None else os.environ
    seen: set[str] = set()
    out: list[str] = []
    for key in PASSWORD_ENV_KEYS:
        val = (src.get(key) or "").strip()
        if val and val not in seen:
            seen.add(val)
            out.append(val)
    return out


def is_google_identifier_url(url: str) -> bool:
    """GSI popup fell through to email/password sign-in (stale Google cookies)."""
    u = (url or "").lower()
    return "accounts.google.com" in u and bool(
        re.search(r"/signin/identifier|/challenge/pwd|/signin/challenge", u)
    )


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



def parse_restriction_lift(text: str) -> datetime | None:
    """Parse LinkedIn 'restriction will be lifted on …' into aware UTC datetime."""
    if not text:
        return None
    m = re.search(
        r"restriction will be lifted on\s+"
        r"([A-Za-z]+\s+\d{1,2},\s+\d{4}\s+\d{1,2}:\d{2}\s*[AP]M)\s*([A-Z]{2,5})",
        text,
        re.I,
    )
    if not m:
        return None
    stamp, tz_raw = m.group(1), m.group(2).upper()
    tz_name = _TZ_ALIASES.get(tz_raw)
    if not tz_name:
        # Fall back to fixed UTC offsets for common LinkedIn abbreviations.
        fixed = {"PDT": -7, "PST": -8, "EDT": -4, "EST": -5, "IST": 5.5, "UTC": 0, "GMT": 0}
        if tz_raw not in fixed:
            return None
        hours = fixed[tz_raw]
        tz = timezone(timedelta(hours=hours))
    else:
        tz = ZoneInfo(tz_name)
    try:
        local = datetime.strptime(stamp.strip(), "%B %d, %Y %I:%M %p").replace(tzinfo=tz)
    except ValueError:
        try:
            local = datetime.strptime(stamp.strip(), "%B %d, %Y %I:%M%p").replace(tzinfo=tz)
        except ValueError:
            return None
    return local.astimezone(timezone.utc)


def _page_body(page, limit: int = 4000) -> str:
    try:
        return page.locator("body").inner_text()[:limit]
    except Exception:
        return ""


def _temp_restriction_info(page) -> dict | None:
    """Detect LinkedIn temporary account restriction (distinct from CAPTCHA)."""
    body = _page_body(page)
    if not re.search(r"temporarily restricted|restriction will be lifted", body, re.I):
        return None
    lift = parse_restriction_lift(body)
    info: dict = {
        "kind": "account_temporarily_restricted",
        "url": page.url,
    }
    if lift is not None:
        now = datetime.now(timezone.utc)
        info["lift_utc"] = lift.isoformat()
        info["seconds_until_lift"] = max(0, int((lift - now).total_seconds()))
    return info


def _wait_out_restriction(info: dict) -> bool:
    """Sleep until lift + buffer when within wait budget. Returns True if waited."""
    secs = info.get("seconds_until_lift")
    if secs is None:
        return False
    wait_for = int(secs) + RESTRICTION_BUFFER_S
    if wait_for <= 0:
        return False
    if wait_for > RESTRICTION_WAIT_MAX_S:
        return False
    print(
        json.dumps(
            {
                "ok": False,
                "reason": "waiting_out_temporary_restriction",
                "lift_utc": info.get("lift_utc"),
                "sleep_s": wait_for,
                "max_s": RESTRICTION_WAIT_MAX_S,
            }
        ),
        flush=True,
    )
    # Chunked sleep so logs stay alive on long waits.
    end = time.time() + wait_for
    while time.time() < end:
        chunk = min(30, end - time.time())
        if chunk <= 0:
            break
        time.sleep(chunk)
    return True


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



def _has_google_session(ctx) -> bool:
    """True when CDP profile has Google login cookie *names* (may still be stale)."""
    try:
        cookies = ctx.cookies(["https://accounts.google.com", "https://www.google.com"])
        names = {c.get("name") for c in cookies}
        return bool(names & {"__Secure-1PSID", "__Secure-3PSID", "SID"})
    except Exception:
        return False


def _page_body(page, limit: int = 1500) -> str:
    try:
        return page.locator("body").inner_text()[:limit]
    except Exception:
        return ""


def _complete_google_password_login(popup, email: str, password: str) -> str:
    """Fill Google identifier / password form. Returns ok|wrong_password|no_form|need_human."""
    if popup is None or not email or not password:
        return "no_form"
    try:
        url = popup.url or ""
    except Exception:
        return "no_form"
    if not is_google_identifier_url(url) and "accounts.google.com" not in url.lower():
        return "no_form"

    email_box = None
    for sel in ("input[type='email']", "input[name='identifier']", "#identifierId"):
        loc = popup.locator(sel)
        try:
            n = min(loc.count(), 5)
        except Exception:
            n = 0
        for i in range(n):
            try:
                el = loc.nth(i)
                if el.is_visible():
                    email_box = el
                    break
            except Exception:
                continue
        if email_box is not None:
            break
    if email_box is not None:
        try:
            email_box.click(timeout=3000)
            email_box.fill("")
            email_box.fill(email)
            nxt = popup.get_by_role("button", name=re.compile(r"^Next$", re.I))
            if nxt.count():
                nxt.first.click(timeout=5000)
            else:
                email_box.press("Enter")
            time.sleep(2.5)
        except Exception:
            return "no_form"

    pass_box = None
    for sel in ("input[type='password']", "input[name='Passwd']", "input[name='password']"):
        loc = popup.locator(sel)
        try:
            n = min(loc.count(), 5)
        except Exception:
            n = 0
        for i in range(n):
            try:
                el = loc.nth(i)
                if el.is_visible():
                    pass_box = el
                    break
            except Exception:
                continue
        if pass_box is not None:
            break
    if pass_box is None:
        body = _page_body(popup)
        if wrong_password_text(body):
            return "wrong_password"
        if re.search(r"verify|2-step|unusual activity|captcha", body, re.I):
            return "need_human"
        return "no_form"
    try:
        pass_box.click(timeout=3000)
        pass_box.fill("")
        pass_box.press_sequentially(password, delay=20)
        nxt = popup.get_by_role("button", name=re.compile(r"^Next$", re.I))
        if nxt.count():
            nxt.first.click(timeout=5000)
        else:
            pass_box.press("Enter")
        time.sleep(2.5)
    except Exception:
        return "no_form"
    body = _page_body(popup)
    if wrong_password_text(body):
        return "wrong_password"
    if re.search(r"verify|2-step|unusual activity|captcha", body, re.I):
        return "need_human"
    return "ok"


def _reveal_full_login_form(page) -> None:
    """Leave LinkedIn 'Welcome back' remembered-account UI so GSI is clickable.

    The welcome-back card shows password + Apple only; Continue with Google lives
    on the full /login form behind 'Sign in using another account'.
    """
    try:
        body = page.locator("body").inner_text()[:1200]
    except Exception:
        body = ""
    if not re.search(r"Welcome back|Sign in using another account", body, re.I):
        return
    try:
        link = page.get_by_role("link", name=re.compile(r"Sign in using another account", re.I))
        if link.count() and link.first.is_visible():
            link.first.click(timeout=5000)
            time.sleep(2)
            return
    except Exception:
        pass
    try:
        alt = page.locator("a:has-text('Sign in using another account')")
        if alt.count():
            alt.first.click(force=True, timeout=5000)
            time.sleep(2)
    except Exception:
        pass


def _gsi_button_frames(page):
    frames = [f for f in page.frames if "accounts.google.com/gsi/button" in (f.url or "")]
    # Prefer a frame whose Continue button is actually visible (width~400).
    visible = []
    for fr in frames:
        try:
            btn = fr.locator("div[role=button]").first
            if btn.count() and btn.is_visible():
                visible.append(fr)
        except Exception:
            continue
    return visible or frames


def _click_continue_google(ctx, page) -> bool:
    """Click LinkedIn Continue with Google and choose the remembered Google account."""
    _reveal_full_login_form(page)
    # Wait briefly for GSI iframes after welcome-back → full form transition.
    deadline = time.time() + 8
    frames = _gsi_button_frames(page)
    while not frames and time.time() < deadline:
        time.sleep(0.5)
        frames = _gsi_button_frames(page)
    popup = None
    clicked = False

    def _do_click():
        nonlocal clicked, frames
        frames = _gsi_button_frames(page)
        for fr in frames:
            try:
                fr.locator("div[role=button]").first.click(force=True, timeout=8000)
                clicked = True
                return
            except Exception:
                continue
        btn = page.locator("[role=button]:has-text('Continue with Google')")
        try:
            n = min(btn.count(), 6)
        except Exception:
            n = 0
        for i in range(n):
            try:
                el = btn.nth(i)
                if el.is_visible():
                    el.click(force=True, timeout=8000)
                    clicked = True
                    return
            except Exception:
                continue
        if n:
            try:
                btn.first.click(force=True, timeout=8000)
                clicked = True
            except Exception:
                pass

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
        # Popup may already exist from a prior partial click.
        if popup is None:
            for pg in ctx.pages:
                u = pg.url or ""
                if "accounts.google.com" in u and re.search(r"select|gsi|signin", u, re.I):
                    popup = pg
                    break

    if not clicked:
        return False

    if popup is not None:
        try:
            popup.wait_for_load_state("domcontentloaded", timeout=30000)
        except Exception:
            pass
        time.sleep(1.5)
        # Account chooser: remembered Gmail on GSI select card
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
            # Stale Google cookies → identifier/password form instead of chooser.
            if is_google_identifier_url(popup.url or "") or re.search(
                r"Email or phone|Enter your password", _page_body(popup), re.I
            ):
                email = EMAIL or DEFAULT_EMAIL
                ident_result = "no_form"
                for pw in password_candidates():
                    ident_result = _complete_google_password_login(popup, email, pw)
                    if ident_result in ("ok", "need_human"):
                        break
                if ident_result == "wrong_password":
                    try:
                        popup.screenshot(
                            path=str(_art() / "[REDACTED]-auto-login-wrong-password.png"),
                            timeout=8000,
                        )
                    except Exception:
                        pass
                if ident_result != "no_form":
                    return True
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
    page = _pick_linkedin_page(ctx)
    _reveal_full_login_form(page)
    return _pick_linkedin_page(ctx)


def _wait_signed_in(ctx, page, deadline: float, via: str, out: dict) -> int | None:
    """Poll until signed in / captcha / timeout. Returns exit code or None to continue.

    Exit 7 = temporary account restriction (may be waitable).
    Exit 6 = interactive CAPTCHA/checkpoint.
    Exit 8 = explicit wrong-password error (try next candidate).
    """
    while time.time() < deadline:
        page = _pick_linkedin_page(ctx)
        if _cookies_has_li_at(ctx) and _is_signed_in(ctx, page):
            out.update(ok=True, reason=via, url=page.url)
            print(json.dumps(out))
            return 0
        info = _temp_restriction_info(page)
        if info and not _cookies_has_li_at(ctx):
            out.update(ok=False, reason="account_temporarily_restricted", via=via, **info)
            try:
                page.screenshot(path=str(_art() / "linkedin-auto-login-captcha.png"), timeout=8000)
            except Exception:
                pass
            return 7
        body = _page_body(page)
        if wrong_password_text(body) and not _cookies_has_li_at(ctx):
            out["attempts"].append({"step": via, "wrong_password": True})
            try:
                page.screenshot(
                    path=str(_art() / "[REDACTED]-auto-login-wrong-password.png"),
                    timeout=8000,
                )
            except Exception:
                pass
            return 8
        if _on_captcha(page) and not _cookies_has_li_at(ctx):
            # Avoid mislabeling temporary restriction pages as CAPTCHA.
            if _temp_restriction_info(page):
                continue
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
    pw_list = password_candidates()
    # Cloud datacenter IPs often CAPTCHA Google SSO; prefer password when set.
    prefer_password = bool(pw_list) and os.environ.get(
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
        google_session = _has_google_session(ctx)
        out["google_session"] = google_session

        def try_password() -> int | None:
            if not pw_list:
                out["attempts"].append(
                    {
                        "step": "password",
                        "skipped": True,
                        "hint": "Set Cursor secrets LINKEDIN_EMAIL + LINKEDIN_PASSWORD for password fallback",  # pragma: allowlist secret
                    }
                )
                return None
            last_rc = None
            for idx, pw in enumerate(pw_list):
                nonlocal_page = _goto_login_clean(ctx, _pick_linkedin_page(ctx))  # pragma: allowlist secret
                out["attempts"].append(
                    {
                        "step": "password",
                        "email": email[:3] + "***",
                        "candidate": idx + 1,
                        "n_candidates": len(pw_list),
                    }
                )
                if not _password_login(nonlocal_page, email, pw):
                    out["attempts"].append({"step": "password", "submitted": False, "candidate": idx + 1})
                    continue
                method_deadline = time.time() + METHOD_TIMEOUT_S
                last_rc = _wait_signed_in(ctx, nonlocal_page, method_deadline, "password", out)
                if last_rc == 0:
                    return 0
                if last_rc in (6, 7):
                    return last_rc
                # 8 = wrong password — try the next unique secret
            return last_rc

        def try_google() -> int | None:
            nonlocal_page = _goto_login_clean(ctx, _pick_linkedin_page(ctx))
            out["attempts"].append({"step": "google_sso", "started": True})
            if not _click_continue_google(ctx, nonlocal_page):
                out["attempts"].append({"step": "google_sso", "clicked": False})
                return None
            out["attempts"].append({"step": "google_sso", "clicked": True})
            method_deadline = time.time() + METHOD_TIMEOUT_S
            return _wait_signed_in(ctx, nonlocal_page, method_deadline, "google_sso", out)

        # Prefer Google SSO when the CDP profile already has Google cookies.
        # Password-first often burns a checkpoint before GSI gets a clean shot;
        # welcome-back UI also hid the GSI button until "another account".
        prefer_google = google_session and os.environ.get(
            "LINKEDIN_PREFER_GOOGLE_IF_SESSION", "1"
        ).strip() not in ("0", "false", "no")
        if prefer_google:
            order = ("google_sso", "password")
        elif prefer_password:
            order = ("password", "google_sso")
        else:
            order = ("google_sso", "password")
        out["order"] = list(order)
        captcha_seen = False
        restriction_info = None
        for step in order:
            rc = try_password() if step == "password" else try_google()
            if rc == 0:
                return 0
            if rc == 7:
                page = _pick_linkedin_page(ctx)
                restriction_info = _temp_restriction_info(page) or {
                    "kind": "account_temporarily_restricted",
                    "url": page.url,
                }
                # Restriction is account-level — other login methods will hit the same wall.
                break
            if rc == 6:
                captcha_seen = True
                # Do not hard-stop — try the other method (password after SSO CAPTCHA).
                continue
            if rc == 8:
                out["wrong_password"] = True
                continue

        # Temporary restriction: wait until lift (within budget) then retry once.
        if restriction_info is None:
            page = _pick_linkedin_page(ctx)
            restriction_info = _temp_restriction_info(page)
        if restriction_info and not _cookies_has_li_at(ctx):
            if _wait_out_restriction(restriction_info):
                out["attempts"].append(
                    {
                        "step": "wait_temporary_restriction",
                        "lift_utc": restriction_info.get("lift_utc"),
                        "slept": True,
                    }
                )
                # Fresh deadline for post-lift retry.
                deadline = time.time() + TIMEOUT_S
                page = _goto_login_clean(ctx, _pick_linkedin_page(ctx))
                for step in order:
                    rc = try_password() if step == "password" else try_google()
                    if rc == 0:
                        return 0
                page = _pick_linkedin_page(ctx)
                if _cookies_has_li_at(ctx) and _is_signed_in(ctx, page):
                    out.update(ok=True, reason="recovered_after_restriction", url=page.url)
                    print(json.dumps(out))
                    return 0
                # Re-check; may still be restricted or flipped to CAPTCHA.
                restriction_info = _temp_restriction_info(page) or restriction_info
            out.update(
                ok=False,
                reason="account_temporarily_restricted",
                url=restriction_info.get("url") or page.url,
                google_session=google_session,
                lift_utc=restriction_info.get("lift_utc"),
                seconds_until_lift=restriction_info.get("seconds_until_lift"),
                hint=(
                    "Temporary LinkedIn restriction; wait until lift_utc then re-run "
                    "(or raise LINKEDIN_RESTRICTION_WAIT_MAX_S)"
                ),
            )
            print(json.dumps(out))
            return 7

        page = _pick_linkedin_page(ctx)
        if _cookies_has_li_at(ctx) and _is_signed_in(ctx, page):
            out.update(ok=True, reason="recovered", url=page.url)
            print(json.dumps(out))
            return 0
        if captcha_seen or (_on_captcha(page) and not _cookies_has_li_at(ctx)):
            out.update(
                ok=False,
                reason="captcha_checkpoint",
                url=page.url,
                google_session=google_session,
                hint=(
                    "Owner CAPTCHA/checkpoint required"
                    if google_session
                    else "CAPTCHA with no Google session — bash scripts/home-headed-login.sh linkedin"
                ),
            )
            print(json.dumps(out))
            return 6

        out.update(
            ok=False,
            reason="linkedin_login_required",
            url=page.url,
            has_li_at=_cookies_has_li_at(ctx),
            google_session=google_session,
            hint="CAPTCHA/checkpoint or Google SSO failed; set Cursor secret LINKEDIN_PASSWORD and re-run",  # pragma: allowlist secret
        )
        wrong_pw = bool(out.get("wrong_password")) or any(
            isinstance(a, dict) and a.get("wrong_password") for a in out.get("attempts") or []
        )
        if wrong_pw:
            out["reason"] = "wrong_password"
            out["password_candidates"] = len(pw_list)
            out["hint"] = (
                "Portal/Google rejected the configured password secret(s). "
                "Update Cursor secret LINKEDIN_PASSWORD (and optionally GOOGLE_PASSWORD) "  # pragma: allowlist secret
                "or run: bash scripts/home-headed-login.sh linkedin"  # pragma: allowlist secret
            )
        print(json.dumps(out))
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
