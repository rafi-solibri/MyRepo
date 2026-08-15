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
    captcha_solver_configured,
    extract_sitekey_from_text,
    inject_hcaptcha_token,
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

assert_true(not inject_hcaptcha_token(object(), ""), "short token rejected")
assert_true(not inject_hcaptcha_token(object(), "short"), "short token rejected 2")

print("tools/ats/test_captcha_solve.py OK")
