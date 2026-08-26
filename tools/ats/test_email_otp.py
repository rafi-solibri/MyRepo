#!/usr/bin/env python3
"""Unit checks for ATS mailbox OTP helpers (no live Gmail)."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.ats.email_otp import (
    extract_otp_candidates,
    gmail_session_known_dead,
    mailbox_unavailable_for_otp,
    mark_gmail_login_required,
    page_shows_otp_wall,
    reset_gmail_login_flag,
)


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


# Prefer contextual 6-digit over bare years / noise.
_oracle = (
    "Confirm Your Identity\n"
    "The verification code was sent to this email address: a@b.com\n"
    "Your verification code is 482193. Enter the code into the field."
)
codes = extract_otp_candidates(_oracle)
assert_true(codes and codes[0] == "482193", f"oracle code got {codes}")

_gh = "Your Greenhouse verification code: 917204\nThis code expires in 10 minutes."
assert_true(extract_otp_candidates(_gh)[0] == "917204", "greenhouse")

_year = "Applied in 2026 for role; no code here."
assert_true("2026" not in extract_otp_candidates(_year), "year not otp")

_bare = "Hello\n391847\nThanks"
assert_true(extract_otp_candidates(_bare)[0] == "391847", "bare 6-digit")


class _FakePage:
    def __init__(self, text: str):
        self._text = text

    def locator(self, _sel: str):
        page = self

        class _Loc:
            def inner_text(self, timeout: int = 0):
                return page._text

        return _Loc()


assert_true(
    page_shows_otp_wall(
        _FakePage("Confirm Your Identity\nThe verification code was sent")
    ),
    "oracle wall",
)
assert_true(
    not page_shows_otp_wall(_FakePage("Email Address\nI agree with the terms\nNEXT")),
    "pre-otp form is not wall",
)

# Cross-process Gmail Sign-in flag: abort OTP wait when mailbox is unreachable.
reset_gmail_login_flag()
assert_true(not gmail_session_known_dead(), "flag clear")
assert_true(not mailbox_unavailable_for_otp(), "available before mark")
mark_gmail_login_required()
assert_true(gmail_session_known_dead(), "flag set")
# Without GMAIL_APP_PASSWORD in env, mailbox is unavailable.
assert_true(mailbox_unavailable_for_otp(), "unavailable after mark without IMAP")
reset_gmail_login_flag()
assert_true(not gmail_session_known_dead(), "flag reset")

print("tools/ats/test_email_otp.py OK")
