#!/usr/bin/env python3
"""Indeed Google SSO heal when Passport cookies are expired / Sign-in wall.

Uses GOOGLE_PASSWORD only (never LINKEDIN_PASSWORD). Password form at
`/signin/challenge/pwd` is filled first; ASK_OWNER_GOOGLE_2FA only for real
2FA (totp / phone prompt).

Wired from uc_daily_apply after restore_signed_in hits a login wall.
"""

from __future__ import annotations

import os
import re
import time
from typing import Any

from tools.google_2fa_prompt import (
    is_google_2fa_challenge,
    is_google_password_challenge,
    wait_owner_google_2fa,
)

WRONG_PASSWORD_RE = re.compile(
    r"wrong password|that.?s not the right password|incorrect password|"
    r"couldn.?t sign you in|wrong email or password",
    re.I,
)


def google_email() -> str:
    return (
        os.environ.get("GOOGLE_EMAIL")
        or os.environ.get("LINKEDIN_EMAIL")
        or os.environ.get("APPLY_EMAIL")
        or ""
    ).strip()


def google_password_candidates(env: dict | None = None) -> list[str]:
    """Gmail SSO passwords only — never LINKEDIN_PASSWORD."""
    src = env if env is not None else os.environ
    out: list[str] = []
    seen: set[str] = set()
    for key in ("GOOGLE_PASSWORD", "GMAIL_PASSWORD"):
        val = (src.get(key) or "").strip()
        if val and val not in seen:
            seen.add(val)
            out.append(val)
    return out


def _snap(sb: Any) -> tuple[str, str, str]:
    try:
        return (
            (sb.get_text("body") or "")[:2500],
            sb.get_title() or "",
            sb.get_current_url() or "",
        )
    except Exception:
        return "", "", ""


def _switch_to_google_window(sb: Any) -> bool:
    """Focus a Google accounts window if SSO opened a popup."""
    try:
        handles = list(sb.driver.window_handles)
    except Exception:
        return False
    for h in handles:
        try:
            sb.driver.switch_to.window(h)
            url = sb.get_current_url() or ""
            if "accounts.google.com" in url.lower():
                return True
        except Exception:
            continue
    return False


_GOOGLE_SSO_CTA_RE = re.compile(
    r"continue with google|sign in with google|sign in to indeed with google",
    re.I,
)


def google_sso_cta_visible_from_text(body: str) -> bool:
    """True when Indeed/Google SSO CTA copy is on the page (homepage modal or auth)."""
    return bool(_GOOGLE_SSO_CTA_RE.search(body or ""))


def looks_indeed_auth_surface(url: str = "", title: str = "", body: str = "") -> bool:
    """True on Sign In | Indeed Accounts /auth — not a signed-in session."""
    blob = f"{url}\n{title}\n{body}".lower()
    return bool(
        re.search(
            r"sign in \| indeed|secure\.indeed\.com/auth|/account/login|"
            r"ready to take the next step",
            blob,
        )
    )


def looks_google_gsi_continue(url: str = "", title: str = "", body: str = "") -> bool:
    """FedCM / Google Identity Services continue after password (2026-09-04)."""
    blob = f"{url}\n{title}\n{body}".lower()
    return bool(
        re.search(
            r"accounts\.google\.com/gsi|fedcm/signincontinue|google identity services",
            blob,
        )
    )


def sso_looks_signed_in(body: str, title: str = "", url: str = "") -> bool:
    """Confirm Indeed Passport session after Google SSO.

    Do not treat Sign-in-wall copy (email address / profile / messages) as
    signed-in — that false-ok'd the 2026-09-04 cloud run while still on /auth.
    """
    if looks_indeed_auth_surface(url, title, body):
        return False
    blob = f"{url}\n{title}\n{body}"
    if re.search(
        r"account settings|sign out of indeed|manage your account security|"
        r"change account type|device management|welcome,\s*\w+",
        blob,
        re.I,
    ):
        return True
    # Soft: signed-in SERP/account chrome, never on an auth URL.
    return bool(
        re.search(r"messages unread|sign out\b", blob, re.I)
        and "create an account or sign in" not in blob.lower()
    )


def _dismiss_cookies(sb: Any) -> str:
    """OneTrust strip covers Continue-with-Google on Sign In | Indeed Accounts."""
    try:
        sb.driver.switch_to.default_content()
    except Exception:
        pass
    try:
        clicked = sb.execute_script(
            """
            const labels = [
              'accept all cookies', 'accept all', 'allow all cookies', 'allow all',
              'reject all cookies', 'reject all', 'i agree', 'got it', 'ok'
            ];
            const els = [...document.querySelectorAll(
              'button, a[role=button], [role=button], input[type=button], input[type=submit]'
            )];
            const textOf = (el) => ((el.innerText || el.value || el.getAttribute('aria-label') || '')).trim().toLowerCase();
            const scored = els.map(el => {
              const t = textOf(el);
              const r = el.getBoundingClientRect();
              const idx = labels.findIndex(l => t === l || t.startsWith(l));
              return {el, t, idx, onScreen: r.width > 0 && r.height > 0};
            }).filter(x => x.idx >= 0 && x.onScreen)
              .sort((a,b) => a.idx - b.idx);
            const hit = scored[0];
            if (!hit) return null;
            try { hit.el.scrollIntoView({block:'center'}); } catch (e) {}
            try { hit.el.click(); } catch (e) {}
            return (hit.el.innerText || hit.el.value || '').trim().slice(0, 80);
            """
        )
        if clicked:
            time.sleep(0.8)
            return str(clicked)
    except Exception:
        return ""
    return ""


def _click_google_sso(sb: Any) -> bool:
    _dismiss_cookies(sb)
    # Homepage modal + auth wall: JS click survives OneTrust overlay / custom buttons.
    try:
        hit = sb.execute_script(
            """
            const labels = [
              'continue with google',
              'sign in with google',
              'sign in to indeed with google',
            ];
            const els = [...document.querySelectorAll(
              'button, a, [role=button], [data-tn-element], [data-provider], [aria-label]'
            )];
            const textOf = (el) => (
              (el.innerText || el.textContent || '') + ' ' +
              (el.getAttribute('aria-label') || '') + ' ' +
              (el.getAttribute('data-tn-element') || '') + ' ' +
              (el.getAttribute('data-provider') || '') + ' ' +
              (el.getAttribute('href') || '')
            ).replace(/\\s+/g, ' ').trim().toLowerCase();
            const scored = els.map(el => {
              const t = textOf(el);
              const r = el.getBoundingClientRect();
              let idx = labels.findIndex(l => t.includes(l));
              // Require a real Google OAuth control — not "Sign in" near a Google logo.
              if (idx < 0 && /accounts\\.google\\.com|data-tn-element.*google|data-provider=.?google/.test(t)) {
                idx = 10;
              }
              return {el, t, idx, onScreen: r.width > 8 && r.height > 8};
            }).filter(x => x.idx >= 0)
              .sort((a,b) => {
                if (a.onScreen !== b.onScreen) return a.onScreen ? -1 : 1;
                return a.idx - b.idx;
              });
            const hit = scored[0];
            if (!hit) return null;
            try { hit.el.scrollIntoView({block:'center'}); } catch (e) {}
            try { hit.el.click(); } catch (e) {}
            return (hit.el.innerText || hit.el.getAttribute('aria-label') || hit.t || '')
              .trim().slice(0, 80);
            """
        )
        if hit:
            time.sleep(2.5)
            if _switch_to_google_window(sb):
                return True
            try:
                cur = (sb.get_current_url() or "").lower()
            except Exception:
                cur = ""
            if "accounts.google.com" in cur:
                return True
            # Click registered but OAuth did not open — keep trying other nodes.
            return False
    except Exception:
        pass
    patterns = (
        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'google')]",
        "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'google')]",
        "//*[@role='button' and contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'google')]",
        "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue with google')]",
        "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign in with google')]",
        "button[data-tn-element*='google']",
        "a[data-tn-element*='google']",
        "[data-tn-element*='google']",
        "[data-provider='google']",
        "[aria-label*='Google']",
        "a[href*='accounts.google.com']",
        "a[href*='google'][href*='oauth']",
    )
    for _ in range(3):
        _dismiss_cookies(sb)
        for sel in patterns:
            try:
                if sb.is_element_visible(sel):
                    sb.click(sel)
                    time.sleep(2.5)
                    return True
            except Exception:
                continue
        time.sleep(1.2)
    return False


def _fill_identifier(sb: Any, email: str) -> bool:
    for sel in (
        "input[type='email']",
        "input[name='identifier']",
        "#identifierId",
    ):
        try:
            if not sb.is_element_visible(sel):
                continue
            sb.type(sel, email)
            time.sleep(0.4)
            for nxt in ("#identifierNext", "button:contains('Next')", "//button[.='Next']"):
                try:
                    if sb.is_element_visible(nxt):
                        sb.click(nxt)
                        time.sleep(2)
                        return True
                except Exception:
                    continue
            try:
                sb.press_keys(sel, "\n")
                time.sleep(2)
                return True
            except Exception:
                return True
        except Exception:
            continue
    return False


def _fill_password(sb: Any, password: str) -> str:
    """Fill Google password. Returns ok|wrong_password|no_field."""
    box = None
    for sel in (
        "input[name='Passwd']",
        "input[type='password']",
        "input[autocomplete*='current-password']",
    ):
        try:
            if sb.is_element_visible(sel):
                box = sel
                break
        except Exception:
            continue
    if not box:
        return "no_field"
    try:
        sb.type(box, password)
        time.sleep(0.3)
        for nxt in ("#passwordNext", "button:contains('Next')", "//button[.='Next']"):
            try:
                if sb.is_element_visible(nxt):
                    sb.click(nxt)
                    break
            except Exception:
                continue
        else:
            try:
                sb.press_keys(box, "\n")
            except Exception:
                pass
        time.sleep(2.5)
    except Exception:
        return "no_field"
    body, _title, url = _snap(sb)
    if WRONG_PASSWORD_RE.search(body):
        return "wrong_password"
    if is_google_password_challenge(url=url, body=body) and WRONG_PASSWORD_RE.search(body):
        return "wrong_password"
    return "ok"


def _pick_account_chooser(sb: Any, email: str) -> bool:
    """Click the matching account tile on Google account chooser."""
    needle = (email or "").lower()
    try:
        body = (sb.get_text("body") or "")[:3000]
    except Exception:
        body = ""
    if needle and needle not in body.lower() and "@gmail.com" not in body.lower():
        return False
    # Prefer data-identifier / data-email tiles.
    for attr in ("data-identifier", "data-email"):
        try:
            sel = f"div[{attr}*='@']"
            if sb.is_element_visible(sel):
                # Click first matching tile text containing email local-part.
                tiles = sb.find_elements(sel)
                for el in tiles[:8]:
                    try:
                        t = (el.text or "") + " " + (el.get_attribute(attr) or "")
                        if needle and needle.split("@")[0].lower() in t.lower():
                            el.click()
                            time.sleep(2)
                            return True
                        if "@gmail.com" in t.lower() or "rafi" in t.lower():
                            el.click()
                            time.sleep(2)
                            return True
                    except Exception:
                        continue
        except Exception:
            continue
    return False


def try_google_sso(sb: Any, *, wait_2fa_sec: int | None = None) -> dict:
    """Attempt Continue-with-Google on Indeed Sign-in wall.

    Returns dict with ok + reason. Never invents applies.
    """
    info: dict[str, Any] = {
        "ok": False,
        "tried": [],
        "email": google_email(),
        "hasGooglePassword": bool(google_password_candidates()),
    }
    pws = google_password_candidates()
    if not pws:
        info["reason"] = "missing_google_password"
        info["hint"] = (
            "Set Environment Secret GOOGLE_PASSWORD (Gmail) — "
            "do not reuse LINKEDIN_PASSWORD"
        )
        return info

    # Prefer the current surface first (India home "Continue with Google" modal
    # or Sign In | Indeed Accounts). Navigating away used to drop the homepage
    # modal, then cookie strip hid the auth-page Google CTA.
    try:
        cur = sb.get_current_url() or ""
    except Exception:
        cur = ""
    body0, title0, url0 = _snap(sb)
    info["tried"].append(
        {
            "before": {
                "url": url0[:160],
                "title": title0[:80],
                "cta": google_sso_cta_visible_from_text(body0),
                "cookieBanner": bool(
                    re.search(r"accept all cookies|reject all", body0, re.I)
                ),
            }
        }
    )
    if "accounts.google.com" not in cur.lower():
        clicked = _click_google_sso(sb)
        info["tried"].append({"google_sso_click": clicked, "where": "current"})
        if not clicked:
            if "secure.indeed.com" not in cur.lower() and "account/login" not in cur.lower():
                try:
                    sb.uc_open_with_reconnect(
                        "https://secure.indeed.com/auth?hl=en_IN&co=IN"
                        "&continue=https%3A%2F%2Fin.indeed.com%2F",
                        5,
                    )
                    time.sleep(2)
                    info["tried"].append({"open_auth": True})
                except Exception as exc:
                    info["tried"].append({"open_auth": str(exc)[:120]})
                clicked = _click_google_sso(sb)
                info["tried"].append({"google_sso_click": clicked, "where": "auth"})
        if not clicked:
            info["reason"] = "google_sso_button_missing"
            try:
                shot = "/opt/cursor/artifacts/indeed-google-sso-missing.png"
                sb.save_screenshot(shot)
                info["screenshot"] = shot
            except Exception:
                pass
            try:
                b, t, u = _snap(sb)
                info["tried"].append(
                    {"missingAt": {"url": u[:160], "title": t[:80], "body": b[:240]}}
                )
            except Exception:
                pass
            return info
        # Click is not enough — wait for accounts.google.com (popup or same tab).
        opened = False
        for _ in range(8):
            if _switch_to_google_window(sb):
                opened = True
                break
            try:
                if "accounts.google.com" in (sb.get_current_url() or "").lower():
                    opened = True
                    break
            except Exception:
                pass
            time.sleep(0.6)
        info["tried"].append({"google_window": opened})
        if not opened:
            info["reason"] = "google_sso_did_not_open"
            try:
                shot = "/opt/cursor/artifacts/indeed-google-sso-missing.png"
                sb.save_screenshot(shot)
                info["screenshot"] = shot
            except Exception:
                pass
            return info

    body, title, url = _snap(sb)
    info["tried"].append({"after_click": {"url": url[:120], "title": title[:80]}})

    # Account chooser
    if "accountchooser" in url.lower() or "Choose an account" in body:
        picked = _pick_account_chooser(sb, info["email"])
        info["tried"].append({"account_chooser": picked})
        time.sleep(1.5)
        body, title, url = _snap(sb)

    # Identifier
    if re.search(r"/signin/identifier|Email or phone", f"{url}\n{body}", re.I):
        filled = _fill_identifier(sb, info["email"])
        info["tried"].append({"identifier": filled})
        time.sleep(1.5)
        body, title, url = _snap(sb)

    # Password (challenge/pwd) — NOT 2FA
    pwd_needed = is_google_password_challenge(url=url, body=body)
    if not pwd_needed:
        try:
            pwd_needed = any(
                sb.is_element_visible(sel)
                for sel in (
                    "input[name='Passwd']",
                    "input[type='password']",
                )
            )
        except Exception:
            pwd_needed = False

    if pwd_needed:
        result = "no_field"
        for pw in pws:
            result = _fill_password(sb, pw)
            info["tried"].append({"password_fill": result})
            if result == "ok":
                break
            if result == "wrong_password":
                info["reason"] = "google_wrong_password"
                info["hint"] = (
                    "GOOGLE_PASSWORD rejected — update Environment Secret "
                    "(do not alias LINKEDIN_PASSWORD)"
                )
                return info
        if result != "ok":
            info["reason"] = f"google_password_{result}"
            return info
        body, title, url = _snap(sb)

    def _click_gsi_continue() -> str:
        for sel in (
            "//button[normalize-space()='Continue']",
            "//button[contains(., 'Continue as')]",
            "//button[normalize-space()='Allow']",
            "//button[normalize-space()='Confirm']",
            "//button[normalize-space()='Next']",
            "//*[@role='button' and contains(., 'Continue')]",
            "button[jsname]",
        ):
            try:
                if sb.is_element_visible(sel):
                    sb.click(sel)
                    time.sleep(1.2)
                    return sel
            except Exception:
                continue
        try:
            hit = sb.execute_script(
                """
                const labels = ['continue as', 'continue', 'allow', 'confirm', 'next'];
                const els = [...document.querySelectorAll('button, [role=button], div[role=button]')];
                const textOf = (el) => ((el.innerText || el.getAttribute('aria-label') || '')).trim().toLowerCase();
                const scored = els.map(el => {
                  const t = textOf(el);
                  const idx = labels.findIndex(l => t === l || t.startsWith(l));
                  const r = el.getBoundingClientRect();
                  return {el, t, idx, onScreen: r.width > 8 && r.height > 8};
                }).filter(x => x.idx >= 0 && x.onScreen).sort((a,b) => a.idx - b.idx);
                if (!scored[0]) return null;
                scored[0].el.click();
                return scored[0].t.slice(0, 80);
                """
            )
            if hit:
                time.sleep(1.2)
                return str(hit)
        except Exception:
            pass
        return ""

    # Real 2FA only after password clears
    if is_google_2fa_challenge(url=url, body=body):
        wait = int(
            wait_2fa_sec
            if wait_2fa_sec is not None
            else os.environ.get("GOOGLE_2FA_WAIT_SEC", "300")
        )
        info["tried"].append({"google_2fa": True, "wait_sec": wait})
        # SeleniumBase page shim for wait_owner_google_2fa (needs .url + locator).
        class _SbPage:
            def __init__(self, driver_sb: Any):
                self._sb = driver_sb

            @property
            def url(self) -> str:
                try:
                    return self._sb.get_current_url() or ""
                except Exception:
                    return ""

            def bring_to_front(self) -> None:
                return None

            def locator(self, sel: str):  # noqa: ANN001
                class _Loc:
                    def __init__(self, s: Any):
                        self._sb = s

                    def inner_text(self, timeout: int = 2000) -> str:  # noqa: ARG002
                        try:
                            return (self._sb.get_text("body") or "")[:2500]
                        except Exception:
                            return ""

                return _Loc(self._sb)

        ok = wait_owner_google_2fa(_SbPage(sb), portal="indeed", wait_sec=wait)
        if not ok:
            info["reason"] = "google_2fa_timeout"
            return info
        body, title, url = _snap(sb)

    # Stay on Google until FedCM/GSI continue + 2FA finish. Jumping to Indeed
    # settings mid-GSI left 2026-09-04 on gsi/fedcm/signincontinue unconfirmed.
    for i in range(12):
        _switch_to_google_window(sb)
        body, title, url = _snap(sb)
        info["tried"].append(
            {"settle": i, "url": url[:160], "title": title[:80]}
        )
        if looks_indeed_auth_surface(url, title, body):
            break
        if sso_looks_signed_in(body, title, url):
            break
        if "indeed.com" in (url or "").lower() and "accounts.google.com" not in (
            url or ""
        ).lower():
            break
        if is_google_2fa_challenge(url=url, body=body):
            wait = int(
                wait_2fa_sec
                if wait_2fa_sec is not None
                else os.environ.get("GOOGLE_2FA_WAIT_SEC", "300")
            )
            info["tried"].append({"google_2fa": True, "wait_sec": wait, "when": "settle"})
            class _SbPage2:
                def __init__(self, driver_sb: Any):
                    self._sb = driver_sb

                @property
                def url(self) -> str:
                    try:
                        return self._sb.get_current_url() or ""
                    except Exception:
                        return ""

                def bring_to_front(self) -> None:
                    return None

                def locator(self, sel: str):  # noqa: ANN001
                    class _Loc:
                        def __init__(self, s: Any):
                            self._sb = s

                        def inner_text(self, timeout: int = 2000) -> str:  # noqa: ARG002
                            try:
                                return (self._sb.get_text("body") or "")[:2500]
                            except Exception:
                                return ""

                    return _Loc(self._sb)

            if not wait_owner_google_2fa(_SbPage2(sb), portal="indeed", wait_sec=wait):
                info["reason"] = "google_2fa_timeout"
                return info
            continue
        if looks_google_gsi_continue(url, title, body) or "accounts.google.com" in (
            url or ""
        ).lower():
            hit = _click_gsi_continue()
            if hit:
                info["tried"].append({"gsi_continue": hit})
        time.sleep(1.4)

    # Prefer Indeed window once Google is done
    try:
        for h in list(sb.driver.window_handles):
            sb.driver.switch_to.window(h)
            u = sb.get_current_url() or ""
            if "indeed.com" in u.lower() and "accounts.google.com" not in u.lower():
                break
    except Exception:
        pass

    body, title, url = _snap(sb)
    if looks_google_gsi_continue(url, title, body) or (
        "accounts.google.com" in (url or "").lower()
        and not sso_looks_signed_in(body, title, url)
    ):
        # FedCM / phone prompt: owner must tap Continue or Yes.
        wait = int(
            wait_2fa_sec
            if wait_2fa_sec is not None
            else os.environ.get("GOOGLE_2FA_WAIT_SEC", "300")
        )
        info["tried"].append({"gsi_owner_wait": True, "wait_sec": wait})
        from tools.google_2fa_prompt import prompt_google_2fa_in_chat

        prompt_google_2fa_in_chat(
            "indeed",
            wait_sec=wait,
            detail="Google Identity Services / FedCM — tap Continue or approve the phone prompt",
        )
        deadline = time.time() + wait
        while time.time() < deadline:
            _switch_to_google_window(sb)
            hit = _click_gsi_continue()
            if hit:
                info["tried"].append({"gsi_continue": hit, "when": "owner_wait"})
            body, title, url = _snap(sb)
            if sso_looks_signed_in(body, title, url):
                break
            if "indeed.com" in (url or "").lower() and "accounts.google.com" not in (
                url or ""
            ).lower():
                break
            time.sleep(3)
        info["tried"].append(
            {"after_gsi_wait": {"url": url[:160], "title": title[:80]}}
        )

    if not sso_looks_signed_in(body, title, url) and not looks_google_gsi_continue(
        url, title, body
    ):
        try:
            sb.uc_open_with_reconnect(
                "https://secure.indeed.com/settings/account", 5
            )
            time.sleep(2)
        except Exception:
            pass
        body, title, url = _snap(sb)
    signed = sso_looks_signed_in(body, title, url)
    info["ok"] = signed
    info["url"] = url[:160]
    info["title"] = title[:80]
    info["reason"] = "signed_in" if signed else "sso_unconfirmed"
    return info
