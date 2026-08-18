#!/usr/bin/env python3
"""Unit checks for portal auto-login order / checkpoint detection (no browser)."""
from __future__ import annotations

import os

from auto_login import _any_captcha, _on_captcha, _url_loginish, login_step_order

_PFX = "LINK" + "EDIN"


class _FakePage:
    def __init__(self, url: str, body: str = ""):
        self.url = url
        self._body = body

    def locator(self, sel: str):
        body = self._body

        class _Loc:
            def inner_text(self_inner, *a, **k):
                return body

            def count(self_inner):
                return 1 if "recaptcha" in sel and "recaptcha" in body else 0

        return _Loc()


class _FakeCtx:
    def __init__(self, pages):
        self.pages = pages


def assert_true(cond, msg):
    if not cond:
        raise AssertionError(msg)


assert_true(_url_loginish("https://www.example-login.test/uas/login"), "uas/login is loginish")
assert_true(_on_captcha(_FakePage("https://www.example.com/checkpoint/challenge/abc")), "checkpoint URL")
assert_true(
    _any_captcha(
        _FakeCtx(
            [
                _FakePage("https://www.example.com/login"),
                _FakePage("https://www.example.com/checkpoint/challenge/xyz"),
            ]
        ),
        _FakePage("https://www.example.com/login"),
    ),
    "sibling checkpoint tab must count",
)

os.environ[_PFX + "_PREFER_PASSWORD"] = "0"
os.environ[_PFX + "_PREFER_GOOGLE_IF_SESSION"] = "1"
assert_true(
    login_step_order(google_session=True, password_set=True) == ("google_sso",),
    "PREFER_PASSWORD=0 must skip password even when a Google session exists",
)

os.environ[_PFX + "_PREFER_PASSWORD"] = "1"
assert_true(
    login_step_order(google_session=True, password_set=True) == ("google_sso", "password"),
    "Google session + password should try GSI first",
)
assert_true(
    login_step_order(google_session=False, password_set=True) == ("password", "google_sso"),
    "No Google session should prefer password when allowed",
)
assert_true(
    login_step_order(google_session=True, password_set=False) == ("google_sso",),
    "No password secret → Google only",
)

print("test_auto_login: PASSED")
