"""Unit tests for temporary-restriction parsing (no CDP)."""

from __future__ import annotations

import importlib.util
import sys
import types
from datetime import datetime, timezone
from pathlib import Path

# Stub playwright so auto_login imports cleanly in CI without browser deps.
sys.modules.setdefault("playwright", types.ModuleType("playwright"))
sys.modules.setdefault("playwright.sync_api", types.ModuleType("playwright.sync_api"))
sys.modules["playwright.sync_api"].sync_playwright = lambda: None

_SPEC = importlib.util.spec_from_file_location(
    "linkedin_auto_login",
    Path(__file__).resolve().parent / "auto_login.py",
)
_mod = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_mod)
parse_restriction_lift = _mod.parse_restriction_lift


def test_parse_pdt_lift_to_utc():
    body = (
        "Your account has been temporarily restricted due to unusually high "
        "volume of LinkedIn profile data. Your restriction will be lifted on "
        "August 18, 2026 9:09 PM PDT."
    )
    lift = parse_restriction_lift(body)
    assert lift == datetime(2026, 8, 19, 4, 9, tzinfo=timezone.utc)


def test_parse_missing_returns_none():
    assert parse_restriction_lift("Quick security check") is None


def test_wrong_password_text_portal_and_google():
    assert _mod.wrong_password_text("That’s not the right password.")
    assert _mod.wrong_password_text("That's not the right password.")
    assert _mod.wrong_password_text("Wrong email or password.")
    assert _mod.wrong_password_text(
        'Wrong password. Try again or click "Try another way" for more options.'
    )
    assert _mod.wrong_password_text("Wrong email or password.")
    assert not _mod.wrong_password_text("Welcome back\nPassword\nSign in")


def test_password_candidates_unique_and_ordered():
    env = {
        "LINKEDIN_PASSWORD": "short9xx",  # pragma: allowlist secret
        "GOOGLE_PASSWORD": "gmail-only-pwd",
        "NAUKRI_WORKDAY_PASSWORD": "longer-workday-18",
        "ATS_PASSWORD": "longer-workday-18",
        "WORKDAY_PASSWORD": "",
    }
    # LinkedIn path must never include GOOGLE_PASSWORD.
    got = _mod.password_candidates(env)
    assert got == ["short9xx", "longer-workday-18"]
    assert _mod.linkedin_password_candidates(env) == got
    assert _mod.password_candidates({}) == []


def test_google_vs_linkedin_password_routing():
    env = {
        "LINKEDIN_PASSWORD": "li-secret-9",  # pragma: allowlist secret
        "GOOGLE_PASSWORD": "gmail-secret-19xx",
        "NAUKRI_WORKDAY_PASSWORD": "workday-fallback-18",
    }
    assert _mod.google_password_candidates(env) == ["gmail-secret-19xx"]
    assert "li-secret-9" not in _mod.google_password_candidates(env)
    li = _mod.linkedin_password_candidates(env)
    assert li[0] == "li-secret-9"
    assert "gmail-secret-19xx" not in li
    assert _mod.google_password_candidates({}) == []


def test_is_google_identifier_url():
    assert _mod.is_google_identifier_url(
        "https://accounts.google.com/v3/signin/identifier?continue=https://accounts.google.com/gsi/select"
    )
    assert _mod.is_google_identifier_url(
        "https://accounts.google.com/v3/signin/challenge/pwd?TL=abc"
    )
    assert not _mod.is_google_identifier_url(
        "https://accounts.google.com/v3/signin/challenge/totp?TL=abc"
    )
    assert not _mod.is_google_identifier_url(
        "https://accounts.google.com/signin/challenge/ipp"
    )
    assert not _mod.is_google_identifier_url("https://accounts.google.com/gsi/select")
    assert not _mod.is_google_identifier_url("https://www.example.com/login")


def test_page_needs_google_password_url_and_body():
    class FakePage:
        def __init__(self, url: str, body: str = ""):
            self.url = url
            self._body = body

        def locator(self, sel):
            raise AssertionError("unused")

    assert _mod._page_needs_google_password(
        FakePage("https://accounts.google.com/v3/signin/challenge/pwd?TL=x")
    )
    assert _mod._page_needs_google_password(
        FakePage(
            "https://accounts.google.com/signin/v2/challenge/pwd",
            "Enter your password",
        )
    )
    # Monkeypatch body reader for non-identifier URL with password copy.
    orig = _mod._page_body
    _mod._page_body = lambda p: getattr(p, "_body", "")
    try:
        assert _mod._page_needs_google_password(
            FakePage("https://accounts.google.com/signin/oauth", "Enter your password")
        )
        assert not _mod._page_needs_google_password(
            FakePage("https://accounts.google.com/gsi/select", "Choose an account")
        )
    finally:
        _mod._page_body = orig


def test_google_auth_pages_filters():
    class FakeCtx:
        def __init__(self, urls):
            self.pages = [types.SimpleNamespace(url=u) for u in urls]

    pages = _mod._google_auth_pages(
        FakeCtx(
            [
                "https://www.linkedin.com/login",
                "https://accounts.google.com/v3/signin/identifier?hl=en",
                "https://accounts.google.com/gsi/select",
                "https://www.google.com/",
            ]
        )
    )
    assert len(pages) == 2
    assert "identifier" in pages[0].url
    assert "gsi/select" in pages[1].url
