#!/usr/bin/env python3
"""Unit checks for ATS captcha solver helpers (no live API)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.ats.captcha_solve import (
    _captcha_poll_frames,
    captcha_solver_configured,
    extract_sitekey_from_text,
    inject_hcaptcha_token,
    owner_captcha_wait_sec,
    owner_hcaptcha_cleared,
)


def assert_true(cond, msg):
    if not cond:
        raise AssertionError(msg)


assert_true(
    extract_sitekey_from_text('<div class="h-captcha" data-sitekey="10000000-ffff-ffff-ffff-000000000001"></div>')
    == "10000000-ffff-ffff-ffff-000000000001",
    "data-sitekey",
)
assert_true(
    extract_sitekey_from_text(
        "https://newassets.hcaptcha.com/captcha/v1/x/static/hcaptcha.html?sitekey=a1b2c3d4e5f6abcd"
    )
    == "a1b2c3d4e5f6abcd",
    "iframe sitekey query",
)
assert_true(not extract_sitekey_from_text("no widget here"), "empty")

os.environ.pop("CAPSOLVER_API_KEY", None)
os.environ.pop("TWOCAPTCHA_API_KEY", None)
os.environ.pop("TWO_CAPTCHA_API_KEY", None)
assert_true(not captcha_solver_configured(), "no keys")
os.environ["CAPSOLVER_API_KEY"] = "test-key"
assert_true(captcha_solver_configured(), "capsolver key")
os.environ.pop("CAPSOLVER_API_KEY", None)

_saved = {k: os.environ.get(k) for k in ("ATS_CAPTCHA_WAIT_SEC", "HOME_LOCAL", "CHROME_HEADLESS")}
for k in ("ATS_CAPTCHA_WAIT_SEC", "HOME_LOCAL", "CHROME_HEADLESS"):
    os.environ.pop(k, None)
os.environ["CHROME_HEADLESS"] = "1"
assert_true(owner_captcha_wait_sec() == 0, "cloud headless waits 0")
os.environ["HOME_LOCAL"] = "1"
assert_true(owner_captcha_wait_sec() == 180, "home local default wait")
os.environ["ATS_CAPTCHA_WAIT_SEC"] = "300"
assert_true(owner_captcha_wait_sec() == 300, "explicit wait wins")
os.environ["ATS_CAPTCHA_WAIT_SEC"] = "0"
assert_true(owner_captcha_wait_sec() == 0, "explicit 0 disables wait")
os.environ.pop("ATS_CAPTCHA_WAIT_SEC", None)
os.environ.pop("HOME_LOCAL", None)
os.environ["CHROME_HEADLESS"] = "0"
assert_true(owner_captcha_wait_sec() == 180, "headed chrome default wait")
for k, v in _saved.items():
    if v is None:
        os.environ.pop(k, None)
    else:
        os.environ[k] = v

assert_true(not inject_hcaptcha_token(object(), ""), "short token rejected")
assert_true(not inject_hcaptcha_token(object(), "short"), "short token rejected 2")


class _FakeFrame:
    def __init__(self, url: str):
        self.url = url


class _FakePage:
    def __init__(self, frames):
        self.frames = frames


_page = _FakePage(
    [
        _FakeFrame("https://hyland.icims.com/jobs/..."),
        _FakeFrame("https://newassets.hcaptcha.com/captcha/v1/x/static/hcaptcha.html"),
        _FakeFrame("https://www.google.com/recaptcha/api2/anchor"),
        _FakeFrame("https://hyland.icims.com/jobs/.../login"),
    ]
)
# page itself is first; hcaptcha/recaptcha iframes skipped
_polled = _captcha_poll_frames(_page)
assert_true(_polled[0] is _page, "page first")
assert_true(len(_polled) == 3, f"skip captcha iframes got {len(_polled)}")
assert_true(all("hcaptcha" not in getattr(f, "url", "") for f in _polled[1:]), "no hcaptcha frames")
assert_true(all("recaptcha" not in getattr(f, "url", "") for f in _polled[1:]), "no recaptcha frames")


class _BodyLoc:
    def __init__(self, text: str):
        self._text = text

    def inner_text(self, *a, **k):
        return self._text


class _CountLoc:
    def __init__(self, n: int):
        self._n = n

    def count(self):
        return self._n


class _ClearPage:
    """Minimal page stub for owner_hcaptcha_cleared."""

    def __init__(self, url: str, body: str, *, files: int = 0, token: str = ""):
        self.url = url
        self._body = body
        self._files = files
        self._token = token
        self.frames = [self]

    def set_default_timeout(self, *_a, **_k):
        return None

    def locator(self, sel):
        s = sel or ""
        if "h-captcha-response" in s or "g-recaptcha-response" in s:
            return _CountLoc(1 if self._token else 0)
        if "type='file'" in s or 'type="file"' in s:
            return _CountLoc(self._files)
        if "first" in s.lower() or "legalName" in s or "formField-name" in s:
            return _CountLoc(0)
        if sel == "body" or s == "body":
            return _BodyLoc(self._body)
        return _CountLoc(0)

    def evaluate(self, js, *a, **k):
        # hcaptcha_token_present uses evaluate on frames.
        if self._token and len(self._token) > 20:
            return True
        return False


# Confirmation after owner click must clear immediately (not wait for token).
_sub = _ClearPage(
    "https://careers-hyland.icims.com/jobs/14269/x/job?mode=submit_apply",
    "Your application was submitted successfully. Thank you for applying.\nLog Out",
)
assert_true(
    owner_hcaptcha_cleared(
        _sub,
        start_url="https://careers-hyland.icims.com/jobs/14269/x/login",
    )
    in ("submitted_or_already", "icims_logged_in", "left_icims_login", "icims_apply_flow"),
    "submitted/login after captcha clears wait",
)
_tok = _ClearPage("https://example.com/apply", "captcha", token="x" * 40)
assert_true(owner_hcaptcha_cleared(_tok) == "token", "token still clears")
_wall = _ClearPage(
    "https://careers-hyland.icims.com/jobs/1/login",
    "I accept\nEnter your information\nprotected by hCaptcha",
)
assert_true(owner_hcaptcha_cleared(_wall, start_url=_wall.url) is None, "login wall still waiting")

print("tools/ats/test_captcha_solve.py OK")
