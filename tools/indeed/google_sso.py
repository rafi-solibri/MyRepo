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

GOOGLE_SSO_LABELS = (
    "continue with google",
    "sign in with google",
    "sign in using google",
    "sign in with your google",
)

GOOGLE_SSO_SELECTORS = (
    "button[data-tn-element*='google' i]",
    "a[data-tn-element*='google' i]",
    "[data-tn-element*='google' i]",
    "button[id*='google' i]",
    "button[aria-label*='google' i]",
    "a[aria-label*='google' i]",
    "a[href*='accounts.google.com']",
    "iframe[src*='accounts.google.com']",
    "iframe[title*='Google']",
    "button[data-tn-element='google-auth']",
    "//button[contains(translate(., 'GOOGLE', 'google'), 'google')]",
    "//a[contains(translate(., 'GOOGLE', 'google'), 'google')]",
    "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue with google')]",
    "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign in with google')]",
)

COOKIE_DISMISS_JS = """
const labels = [
  'accept all cookies', 'accept all', 'allow all cookies', 'allow all',
  'reject all cookies', 'reject all', 'i agree', 'got it', 'ok'
];
const byId = document.querySelector(
  '#onetrust-accept-btn-handler, #onetrust-reject-all-handler'
);
if (byId) {
  try { byId.click(); } catch (e) {}
  return (byId.innerText || byId.id || '').trim().slice(0, 80);
}
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

GOOGLE_SSO_CLICK_JS = """
const labels = [
  'continue with google', 'sign in with google',
  'sign in using google', 'sign in with your google'
];
const nodes = [...document.querySelectorAll(
  'button, a, [role=button], [data-tn-element*="google" i], [id*="google" i], [aria-label*="google" i], iframe'
)];
function textOf(el) {
  return [
    el.innerText || '',
    el.getAttribute('aria-label') || '',
    el.getAttribute('data-tn-element') || '',
    el.id || '',
    el.getAttribute('title') || '',
    el.getAttribute('src') || '',
    el.getAttribute('href') || ''
  ].join(' ').replace(/\\s+/g, ' ').trim().toLowerCase();
}
const scored = nodes.map(el => {
  const t = textOf(el);
  const r = el.getBoundingClientRect();
  let score = -1;
  if (labels.some(l => t.includes(l))) score = 0;
  else if ((el.getAttribute('data-tn-element') || '').toLowerCase().includes('google')) score = 1;
  else if (el.tagName === 'IFRAME' && t.includes('google')) score = 2;
  else if (t.includes('google') && /login|auth|sign in|continue|sso/.test(t)) score = 3;
  return {el, t, score, onScreen: r.width > 8 && r.height > 8};
}).filter(x => x.score >= 0)
  .sort((a,b) => a.score - b.score || (Number(b.onScreen) - Number(a.onScreen)));
const hit = scored[0];
if (!hit) return null;
try { hit.el.scrollIntoView({block:'center'}); } catch (e) {}
try { hit.el.click(); } catch (e) {}
return (hit.el.innerText || hit.el.getAttribute('aria-label') || hit.el.id || hit.t)
  .toString().trim().slice(0, 80);
"""


def score_google_sso_candidate(text: str, attrs: dict | None = None) -> int | None:
    """Lower score is a better Google SSO control. None = not a candidate."""
    attrs = {str(k).lower(): str(v or "") for k, v in (attrs or {}).items()}
    blob = " ".join(
        [
            text or "",
            attrs.get("aria-label", ""),
            attrs.get("data-tn-element", ""),
            attrs.get("id", ""),
            attrs.get("title", ""),
            attrs.get("href", ""),
            attrs.get("src", ""),
        ]
    )
    blob = re.sub(r"\s+", " ", blob).strip().lower()
    if "google" not in blob:
        return None
    if any(label in blob for label in GOOGLE_SSO_LABELS):
        return 0
    tn = attrs.get("data-tn-element", "").lower()
    if "google" in tn:
        return 1
    tag = (attrs.get("tag") or "").lower()
    if tag == "iframe":
        return 2
    if any(tok in blob for tok in ("login", "auth", "sign in", "continue", "sso")):
        return 3
    return None


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


def _dismiss_cookie_banner(sb: Any) -> str:
    """OneTrust / cookie strip covers Continue with Google on Sign-in."""
    try:
        sb.driver.switch_to.default_content()
    except Exception:
        pass
    try:
        clicked = sb.execute_script(COOKIE_DISMISS_JS)
        if clicked:
            time.sleep(0.8)
            return str(clicked)
    except Exception:
        pass
    return ""


def _js_click_google_sso(sb: Any) -> str:
    try:
        hit = sb.execute_script(GOOGLE_SSO_CLICK_JS)
        return str(hit or "")
    except Exception:
        return ""


def _click_google_sso(sb: Any) -> bool:
    """Click Continue-with-Google even when a cookie overlay covers the CTA."""
    _dismiss_cookie_banner(sb)
    for _ in range(8):
        hit = _js_click_google_sso(sb)
        if hit:
            time.sleep(2.5)
            return True
        for sel in GOOGLE_SSO_SELECTORS:
            try:
                present = False
                try:
                    present = bool(sb.is_element_present(sel))
                except Exception:
                    present = bool(sb.is_element_visible(sel))
                if not present:
                    continue
                clicked = False
                try:
                    el = sb.find_element(sel)
                    sb.execute_script(
                        "const e=arguments[0];"
                        "try{e.scrollIntoView({block:'center'});}catch(x){}"
                        "e.click();",
                        el,
                    )
                    clicked = True
                except Exception:
                    try:
                        sb.click(sel)
                        clicked = True
                    except Exception:
                        clicked = False
                if clicked:
                    time.sleep(2.5)
                    return True
            except Exception:
                continue
        time.sleep(1.0)
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

    # Ensure we are on Indeed auth / login surface.
    try:
        cur = sb.get_current_url() or ""
    except Exception:
        cur = ""
    if "accounts.google.com" not in cur.lower():
        if "secure.indeed.com" not in cur.lower() and "account/login" not in cur.lower():
            try:
                sb.uc_open_with_reconnect(
                    "https://secure.indeed.com/auth?hl=en_IN&co=IN"
                    "&continue=https%3A%2F%2Fin.indeed.com%2F",
                    5,
                )
                time.sleep(2)
            except Exception as exc:
                info["tried"].append({"open_auth": str(exc)[:120]})

        dismissed = _dismiss_cookie_banner(sb)
        if dismissed:
            info["tried"].append({"cookie_banner": dismissed})
        clicked = _click_google_sso(sb)
        info["tried"].append({"google_sso_click": clicked})
        if not clicked:
            info["reason"] = "google_sso_button_missing"
            info["hint"] = (
                "Sign-in wall loaded but Continue with Google was not clickable "
                "(cookie strip / selector). Refresh Indeed Passport via Desktop "
                "Chrome + sync-chrome-sessions if this persists."
            )
            try:
                shot = "/opt/cursor/artifacts/indeed-google-sso-missing.png"
                sb.save_screenshot(shot)
                info["screenshot"] = shot
            except Exception:
                pass
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

    # Consent / Continue back to Indeed
    for label in ("Continue", "Allow", "Confirm", "Next"):
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
    signed = bool(
        re.search(r"welcome|sign out|account settings|email address", body, re.I)
        and "sign in |" not in body.lower()
    )
    if not signed:
        # Messages nav / myjobs as soft proof
        signed = bool(
            re.search(r"my jobs|messages|profile", body, re.I)
            and "create an account or sign in" not in body.lower()
        )
    info["ok"] = signed
    info["url"] = url[:160]
    info["reason"] = "signed_in" if signed else "sso_unconfirmed"
    return info
