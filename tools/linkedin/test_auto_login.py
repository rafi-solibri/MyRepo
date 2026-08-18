#!/usr/bin/env python3
"""Unit checks for auto-login restriction classification (no browser)."""
from __future__ import annotations

from auto_login import account_restriction_info


def assert_true(cond, msg):
    if not cond:
        raise AssertionError(msg)


BODY = """
Sign in Join now
Your account has been temporarily restricted

We restricted your account because we detected that over time, it has accessed
an unusually high volume of profile data.

Your restriction will be lifted on August 18, 2026 9:09 PM PDT.

Close
"""

info = account_restriction_info(BODY)
assert_true(info is not None, "restriction body must match")
assert_true(info["reason"] == "account_temporarily_restricted", "reason")
assert_true(info["until"] == "August 18, 2026 9:09 PM PDT", f"until={info.get('until')!r}")
assert_true("Owner-only" in info["hint"], "hint should be owner-only")

assert_true(account_restriction_info("Quick security check / not a robot") is None, "captcha-only")
assert_true(account_restriction_info("") is None, "empty")
assert_true(account_restriction_info("Welcome Back") is None, "welcome-back")

print("auto_login restriction self-test OK")
