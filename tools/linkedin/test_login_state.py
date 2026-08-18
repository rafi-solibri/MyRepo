#!/usr/bin/env python3
"""Unit checks for LinkedIn restriction detection and login method order."""
from __future__ import annotations

import os

from login_state import account_restricted_text, login_method_order


def assert_true(cond, msg):
    if not cond:
        raise AssertionError(msg)


BODY = (
    "Your account has been temporarily restricted\n"
    "We restricted your account because we detected that over time, it has "
    "accessed an unusually high volume of LinkedIn profile data.\n"
    "Your restriction will be lifted on August 18, 2026 9:09 PM PDT.\n"
    "Close"
)

assert_true(
    account_restricted_text(BODY) == "August 18, 2026 9:09 PM PDT",
    "must parse restriction lift timestamp",
)
assert_true(
    account_restricted_text("Welcome Back\nEmail or phone") is None,
    "normal login must not look restricted",
)
assert_true(
    account_restricted_text("Quick security check", "https://www.example.com/checkpoint")
    is None,
    "generic checkpoint without restriction copy must not match",
)

os.environ["LINKEDIN_PREFER_GOOGLE_IF_SESSION"] = "1"
os.environ["LINKEDIN_PREFER_PASSWORD"] = "1"
assert_true(
    login_method_order(google_session=True, has_password=True) == ("google_sso",),
    "Google session must not fall through to password",
)
assert_true(
    login_method_order(google_session=False, has_password=True)
    == ("password", "google_sso"),
    "no Google session + password secret → password first",
)
assert_true(
    login_method_order(google_session=False, has_password=False) == ("google_sso",),
    "no password secret → Google only",
)

print("login_state self-test OK")
