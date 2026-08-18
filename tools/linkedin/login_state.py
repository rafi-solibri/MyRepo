"""LinkedIn login-wall classifiers (no browser). Used by auto_login + Easy Apply."""

from __future__ import annotations

import os
import re

RESTRICTED_RE = re.compile(
    r"temporarily restricted|restriction will be lifted|"
    r"unusually high volume of .+ profile data",
    re.I,
)
LIFT_RE = re.compile(
    r"lifted on ([A-Za-z]+ \d{1,2}, \d{4}(?:\s+\d{1,2}:\d{2}\s*[AP]M\s*[A-Z]{2,4})?)",
    re.I,
)


def account_restricted_text(body: str, url: str = "") -> str | None:
    """Return lift-until text (or a generic label) when LinkedIn restricted the account."""
    blob = f"{url or ''}\n{body or ''}"
    if not RESTRICTED_RE.search(blob):
        return None
    m = LIFT_RE.search(blob)
    if m:
        return m.group(1).strip()
    return "temporarily restricted"


def login_method_order(*, google_session: bool, has_password: bool) -> tuple[str, ...]:
    """Which unattended login methods to try, in order.

    When the CDP profile already has Google cookies, only try Continue with Google.
    Password after GSI (or after a restriction/checkpoint) hardens CAPTCHA and
    never lifts an account restriction.
    """
    prefer_google = google_session and os.environ.get(
        "LINKEDIN_PREFER_GOOGLE_IF_SESSION", "1"
    ).strip().lower() not in ("0", "false", "no")
    prefer_password = has_password and os.environ.get(
        "LINKEDIN_PREFER_PASSWORD", "1"
    ).strip().lower() not in ("0", "false", "no")
    if prefer_google:
        return ("google_sso",)
    if prefer_password:
        return ("password", "google_sso")
    return ("google_sso",)
