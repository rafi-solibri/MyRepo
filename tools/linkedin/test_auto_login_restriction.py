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
