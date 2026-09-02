#!/usr/bin/env python3
"""Indeed Google SSO heal when Passport cookies are expired / Sign-in wall.

Uses GOOGLE_PASSWORD only (never LINKEDIN_PASSWORD). Password form at
`/signin/challenge/pwd` is filled first; ASK_OWNER_GOOGLE_2FA only for real
2FA (totp / phone prompt).

Wired from uc_daily_apply after restore_signed_in hits a login wall.
"""

from __future__ import annotations

import json
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
EMPTY_PASSWORD_RE = re.compile(
    r"enter a password|password is required|please enter.+password",
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


GOOGLE_SSO_LABEL_RE = re.compile(
    r"continue with google|sign in with google|sign up with google|"
    r"log in with google|login with google",
    re.I,
)


def looks_like_google_sso_control(
    text: str = "",
    aria: str = "",
    href: str = "",
    data_tn: str = "",
) -> bool:
    """True for Indeed 'Continue with Google' (not random Google Analytics copy)."""
    blob = " ".join(x for x in (text, aria, href, data_tn) if x)
    if not blob:
        return False
    if GOOGLE_SSO_LABEL_RE.search(blob):
        return True
    low = blob.lower()
    if "accounts.google.com" in low or ("oauth" in low and "google" in low):
        return True
    tn = (data_tn or "").lower()
    if "google" in tn and any(k in tn for k in ("auth", "login", "signin", "sign-in", "sso")):
        return True
    return False


def indeed_session_looks_signed_in(body: str, url: str = "") -> bool:
    """Strict Indeed jobseeker session — never treat auth email form as signed-in.

    Regression 2026-09-02: ``email address`` on secure.indeed.com/auth matched
    and uc_daily_apply continued anonymously (did_not_leave_indeed streak).
    """
    u = (url or "").lower()
    if "accounts.google.com" in u:
        return False
    if re.search(r"secure\.indeed\.com/auth|/account/login|signin/challenge", u):
        return False
    blob = f"{url}\n{body}"
    if re.search(r"create an account or sign in|ready to take the next step", blob, re.I):
        return False
    return bool(
        re.search(
            r"account settings|messages unread|manage your account security|"
            r"change account type|device management|privacy settings|"
            r"welcome,\s*\w+|sign out of indeed|unread count",
            blob,
            re.I,
        )
    )


def _dismiss_cookie_banner(sb: Any) -> str:
    """OneTrust strip covers Indeed auth Google CTA (2026-09-02 re-run)."""
    try:
        sb.driver.switch_to.default_content()
    except Exception:
        pass
    try:
        clicked = sb.execute_script(
            """
            const labels = [
              'accept all cookies', 'accept all', 'allow all cookies', 'allow all',
              'reject all cookies', 'reject all', 'i agree', 'got it'
            ];
            const els = [...document.querySelectorAll(
              'button, a[role=button], [role=button], input[type=button], input[type=submit]'
            )];
            const textOf = (el) =>
              ((el.innerText || el.value || el.getAttribute('aria-label') || ''))
                .trim().toLowerCase();
            const scored = els.map(el => {
              const t = textOf(el);
              const r = el.getBoundingClientRect();
              const idx = labels.findIndex(l => t === l || t.startsWith(l));
              return {el, idx, onScreen: r.width > 0 && r.height > 0};
            }).filter(x => x.idx >= 0 && x.onScreen)
              .sort((a,b) => a.idx - b.idx);
            const hit = scored[0];
            if (!hit) return null;
            try { hit.el.click(); } catch (e) {}
            return (hit.el.innerText || hit.el.value || '').trim().slice(0, 80);
            """
        )
        if clicked:
            time.sleep(0.8)
            return str(clicked)
    except Exception:
        pass
    return ""


def _js_click_google_sso(sb: Any) -> str:
    """Click Google SSO even when Selenium visibility is blocked by overlay."""
    try:
        return (
            sb.execute_script(
                """
                const textOf = (el) => [
                  el.innerText, el.textContent, el.value,
                  el.getAttribute('aria-label'), el.getAttribute('title'),
                  el.getAttribute('data-tn-element'),
                  el.getAttribute('data-gnav-element-name'),
                  el.getAttribute('href')
                ].filter(Boolean).join(' ');
                const els = [...document.querySelectorAll(
                  'button, a, [role=button], [data-tn-element], [data-provider]'
                )];
                const hit = els.find(el => {
                  const blob = textOf(el).toLowerCase();
                  if (!blob.includes('google')) return false;
                  if (blob.includes('continue with google') ||
                      blob.includes('sign in with google') ||
                      blob.includes('sign up with google') ||
                      blob.includes('log in with google')) return true;
                  if (blob.includes('accounts.google.com')) return true;
                  const tn = (el.getAttribute('data-tn-element') ||
                              el.getAttribute('data-provider') || '').toLowerCase();
                  return tn.includes('google') &&
                    (tn.includes('auth') || tn.includes('login') ||
                     tn.includes('signin') || tn.includes('sso'));
                });
                if (!hit) return '';
                try { hit.scrollIntoView({block:'center'}); } catch (e) {}
                try { hit.click(); } catch (e) {}
                return (hit.innerText || hit.getAttribute('aria-label') ||
                        hit.getAttribute('data-tn-element') || 'clicked').slice(0, 80);
                """
            )
            or ""
        )
    except Exception:
        return ""


def _click_google_sso(sb: Any) -> bool:
    _dismiss_cookie_banner(sb)
    js_hit = _js_click_google_sso(sb)
    if js_hit:
        time.sleep(2.5)
        return True
    patterns = (
        "//button[contains(translate(., 'GOOGLE', 'google'), 'google')]",
        "//a[contains(translate(., 'GOOGLE', 'google'), 'google')]",
        "//*[contains(translate(@aria-label, 'GOOGLE', 'google'), 'google')]",
        "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue with google')]",
        "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign in with google')]",
        "button[data-tn-element='google-auth']",
        "button[data-tn-element*='google']",
        "a[data-tn-element*='google']",
        "[data-provider='google']",
        "a[href*='accounts.google.com']",
        "a[href*='google'][href*='oauth']",
    )
    for sel in patterns:
        try:
            if sb.is_element_visible(sel) or sb.is_element_present(sel):
                sb.click(sel)
                time.sleep(2.5)
                return True
        except Exception:
            continue
    return False


def _save_sso_debug(sb: Any, suffix: str = "try") -> None:
    art = "/opt/cursor/artifacts"
    try:
        os.makedirs(art, exist_ok=True)
        body, title, url = _snap(sb)
        path = os.path.join(art, f"indeed-google-sso-{suffix}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(
                {"title": title[:120], "url": url[:200], "bodySample": body[:800]},
                fh,
                indent=2,
            )
        try:
            sb.save_screenshot(os.path.join(art, f"indeed-google-sso-{suffix}.png"))
        except Exception:
            pass
    except Exception:
        pass


def _open_indeed_auth(sb: Any) -> None:
    sb.uc_open_with_reconnect(
        "https://secure.indeed.com/auth?hl=en_IN&co=IN"
        "&continue=https%3A%2F%2Fin.indeed.com%2F",
        5,
    )
    time.sleep(2)
    _dismiss_cookie_banner(sb)


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


def _js_set_password(sb: Any, password: str) -> dict:
    """Set the visible Google password input via the native value setter.

    SeleniumBase ``type`` often leaves the v3 FedCM field empty (screenshot:
    red "Enter a password" after Next). Native setter + input events works.
    """
    try:
        return (
            sb.execute_script(
                """
                const pw = arguments[0];
                const els = [...document.querySelectorAll(
                  "input[type='password'], input[name='Passwd'], input[autocomplete*='current-password']"
                )];
                const el = els.find(e => {
                  const r = e.getBoundingClientRect();
                  return r.width > 40 && r.height > 10;
                }) || els[0];
                if (!el) return {ok: false, reason: 'no_field'};
                try { el.scrollIntoView({block:'center'}); } catch (e) {}
                try { el.focus(); el.click(); } catch (e) {}
                const proto = Object.getOwnPropertyDescriptor(
                  window.HTMLInputElement.prototype, 'value');
                if (proto && proto.set) proto.set.call(el, pw);
                else el.value = pw;
                el.dispatchEvent(new Event('input', {bubbles: true}));
                el.dispatchEvent(new Event('change', {bubbles: true}));
                el.dispatchEvent(new KeyboardEvent('keyup', {bubbles: true}));
                return {ok: !!(el.value && el.value.length), len: (el.value || '').length};
                """,
                password,
            )
            or {"ok": False, "reason": "no_field"}
        )
    except Exception as exc:
        return {"ok": False, "reason": str(exc)[:80]}


def _click_google_next(sb: Any) -> bool:
    for nxt in (
        "#passwordNext",
        "//button[normalize-space()='Next']",
        "//div[@role='button' and normalize-space()='Next']",
        "button:contains('Next')",
    ):
        try:
            if sb.is_element_visible(nxt) or sb.is_element_present(nxt):
                sb.click(nxt)
                return True
        except Exception:
            continue
    return False


def _fill_password(sb: Any, password: str) -> str:
    """Fill Google password. Returns ok|wrong_password|empty|no_field."""
    if not password:
        return "no_field"
    filled = _js_set_password(sb, password)
    if not filled.get("ok"):
        # Fallback: Selenium type into a visible box.
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
            sb.click(box)
            sb.type(box, password)
        except Exception:
            return "no_field"
        filled = _js_set_password(sb, password)
        if not filled.get("ok"):
            return "empty"
    time.sleep(0.4)
    if not _click_google_next(sb):
        try:
            sb.press_keys("input[type='password']", "\n")
        except Exception:
            pass
    time.sleep(2.5)
    body, _title, url = _snap(sb)
    if WRONG_PASSWORD_RE.search(body):
        return "wrong_password"
    if EMPTY_PASSWORD_RE.search(body) and is_google_password_challenge(url=url, body=body):
        # Still on pwd with empty-field error — Next fired without a value.
        return "empty"
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

    # Ensure we are on Indeed auth / login surface.
    try:
        cur = sb.get_current_url() or ""
    except Exception:
        cur = ""
    if "accounts.google.com" not in cur.lower():
        cookie = _dismiss_cookie_banner(sb)
        if cookie:
            info["tried"].append({"cookie_banner": cookie})
        # Cookie overlay on settings/account often hides the Google CTA.
        # Try the current Sign-in wall first, then canonical /auth.
        clicked = _click_google_sso(sb)
        info["tried"].append({"google_sso_click": clicked})
        if not clicked:
            try:
                _open_indeed_auth(sb)
                info["tried"].append({"open_auth": True})
            except Exception as exc:
                info["tried"].append({"open_auth": str(exc)[:120]})
            clicked = _click_google_sso(sb)
            info["tried"].append({"google_sso_click_retry": clicked})
        if not clicked:
            _save_sso_debug(sb, "button-missing")
            info["reason"] = "google_sso_button_missing"
            return info
        time.sleep(2)
        _switch_to_google_window(sb)

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

    # Stay on Google until pwd/2FA actually navigates away. Do not click
    # Indeed auth "Next" (email form) — that was a false "consent" in the
    # 2026-09-02 re-run while challenge/pwd was still open in another tab.
    _switch_to_google_window(sb)
    left_pwd = False
    for _ in range(8):
        body, title, url = _snap(sb)
        if "accounts.google.com" not in url.lower():
            left_pwd = True
            break
        if is_google_2fa_challenge(url=url, body=body):
            break
        if is_google_password_challenge(url=url, body=body):
            # Only re-submit if JS can see a non-empty password value.
            again = _js_set_password(sb, pws[0])
            if again.get("ok"):
                _click_google_next(sb)
                info["tried"].append({"password_next_retry": True})
            else:
                info["tried"].append({"password_next_retry": "empty_field"})
        time.sleep(1.5)
    else:
        body, title, url = _snap(sb)

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

    # Google consent only (never Indeed email-form Next).
    if "accounts.google.com" in (url or "").lower():
        for label in ("Continue", "Allow", "Confirm"):
            try:
                sel = f"//button[normalize-space()='{label}']"
                if sb.is_element_visible(sel):
                    sb.click(sel)
                    time.sleep(1.5)
                    info["tried"].append({"consent": label})
            except Exception:
                continue

    # Prefer Indeed window
    try:
        for h in list(sb.driver.window_handles):
            sb.driver.switch_to.window(h)
            u = sb.get_current_url() or ""
            if "indeed.com" in u.lower() and "accounts.google.com" not in u.lower():
                break
    except Exception:
        pass

    try:
        sb.uc_open_with_reconnect(
            "https://secure.indeed.com/settings/account", 5
        )
        time.sleep(2)
    except Exception:
        pass
    body, title, url = _snap(sb)
    signed = indeed_session_looks_signed_in(body, url)
    info["ok"] = signed
    info["url"] = url[:160]
    info["leftGooglePwd"] = left_pwd
    info["reason"] = "signed_in" if signed else "sso_unconfirmed"
    if not signed:
        _save_sso_debug(sb, "unconfirmed")
        info["hint"] = (
            "Google SSO did not reach Indeed account settings — "
            "approve ASK_OWNER_GOOGLE_2FA if prompted, or refresh Passport "
            "via Desktop Chrome + sync-chrome-sessions"
        )
    return info
