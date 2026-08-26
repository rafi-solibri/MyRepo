#!/usr/bin/env python3
"""Unit checks for Google 2FA chat-prompt helpers (no live browser)."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.google_2fa_prompt import is_google_2fa_challenge  # noqa: E402


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


assert_true(
    is_google_2fa_challenge(
        url="https://accounts.google.com/v3/signin/challenge/totp?TL=abc",
        body="Enter the code from your authenticator app",
    ),
    "totp challenge",
)
assert_true(
    is_google_2fa_challenge(
        url="https://accounts.google.com/signin/challenge/ipp",
        body="Check your phone. Google sent a notification.",
    ),
    "phone prompt",
)
assert_true(
    not is_google_2fa_challenge(
        url="https://www.linkedin.com/feed/",
        body="Start a post",
    ),
    "linkedin feed is not 2FA",
)
assert_true(
    not is_google_2fa_challenge(
        url="https://accounts.google.com/signin/identifier",
        body="Email or phone",
    ),
    "identifier alone is not 2FA",
)

print("google_2fa_prompt tests OK")
