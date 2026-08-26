#!/usr/bin/env python3
"""Prompt the owner in chat whenever Google shows a 2FA / authenticator challenge.

Cloud agents run unattended; the owner watches Cursor on mobile. When Google
asks for a 2-step / authenticator / phone prompt code, print a loud banner in
the agent transcript and keep the Chrome tab focused until the challenge
clears (or timeout).

Also used for mailbox-readable email OTPs when the agent wants a human to
confirm — prefer tools/ats/email_otp.py for autofill first.

Usage (from portal helpers):
  from tools.google_2fa_prompt import (
      is_google_2fa_challenge,
      prompt_google_2fa_in_chat,
      wait_owner_google_2fa,
  )
  if is_google_2fa_challenge(page):
      wait_owner_google_2fa(page, portal="linkedin")
"""

from __future__ import annotations

import os
import re
import sys
import time
from typing import Any

# Password / identifier pages are NOT 2FA — do not treat challenge/pwd as a phone prompt.
_PASSWORD_URL_RE = re.compile(
    r"/challenge/pwd|/signin/identifier|/signin/v2/sl/pwd|Email or phone",
    re.I,
)
_2FA_URL_RE = re.compile(
    r"accounts\.google\.com/.*/challenge/(totp|ipp|sk|az|ipe|selection|kpe|dp|bc)",
    re.I,
)
_CHALLENGE_RE = re.compile(
    r"2[- ]step|two[- ]step|authenticator|verification code|"
    r"enter (the |your )?(code|pin) from (your )?(authenticator|phone|app)|"
    r"google prompt|check your phone|tap yes|confirm it.?s you|"
    r"account recovery|verify it.?s you|"
    r"challenge/totp|challenge/ipp|challenge/sk",
    re.I,
)

_DONE_URL_RE = re.compile(
    r"linkedin\.com/(feed|jobs|in/)|hirist\.tech/(applied|jobfeed|myprofile)|"
    r"naukri\.com|foundit\.in|cutshort\.io|instahyre\.com|indeed\.com|"
    r"accounts\.google\.com/(?:b/0/)?(?:ManageAccount|SignOutOptions)",
    re.I,
)


def is_google_2fa_challenge(page: Any = None, *, url: str = "", body: str = "") -> bool:
    """True when the page looks like a Google 2FA / challenge screen."""
    u = url or ""
    text = body or ""
    if page is not None:
        try:
            u = u or (page.url or "")
        except Exception:
            pass
        if not text:
            try:
                text = page.locator("body").inner_text(timeout=2000)[:2500]
            except Exception:
                text = ""
    blob = f"{u}\n{text}"
    # Google password / identifier must never be classified as 2FA.
    if _PASSWORD_URL_RE.search(u) or (
        "accounts.google.com" in u.lower()
        and re.search(r"Enter your password|Wrong password", text, re.I)
        and not _CHALLENGE_RE.search(text)
    ):
        return False
    if _2FA_URL_RE.search(u):
        return True
    if "accounts.google.com" in u.lower() and _CHALLENGE_RE.search(blob):
        return True
    if _CHALLENGE_RE.search(text) and re.search(
        r"google|g-?suite|rafi\.success@gmail", text, re.I
    ):
        return True
    return False


def prompt_google_2fa_in_chat(portal: str, *, wait_sec: int, detail: str = "") -> None:
    """Loud transcript banner so the owner can enter the phone authenticator code."""
    lines = [
        "",
        "=" * 64,
        f"ASK_OWNER_GOOGLE_2FA ({portal})",
        "=" * 64,
        "Google is asking for a 2-factor / authenticator / phone prompt code.",
        "1) Open Google Authenticator (or the Google phone prompt) on your mobile NOW.",
        "2) Type the 6-digit code into the focused Chrome tab (or tap Yes on the phone).",
        "3) Leave this Cursor chat open — the agent is waiting and will continue after success.",
        f"Waiting up to {wait_sec}s for the challenge to clear…",
    ]
    if detail:
        lines.append(f"Detail: {detail[:200]}")
    lines.append("=" * 64)
    lines.append("")
    msg = "\n".join(lines)
    print(msg, flush=True)
    print(msg, file=sys.stderr, flush=True)


def wait_owner_google_2fa(
    page: Any,
    *,
    portal: str,
    wait_sec: int | None = None,
    poll_sec: float | None = None,
) -> bool:
    """Focus the challenge tab, prompt in chat, poll until cleared. Returns True if cleared."""
    wait = int(
        wait_sec
        if wait_sec is not None
        else os.environ.get("GOOGLE_2FA_WAIT_SEC", "300")
    )
    poll = float(
        poll_sec
        if poll_sec is not None
        else os.environ.get("GOOGLE_2FA_POLL_SEC", "3")
    )
    if wait <= 0:
        return False

    try:
        url = page.url or ""
    except Exception:
        url = ""
    prompt_google_2fa_in_chat(portal, wait_sec=wait, detail=url)

    # Keep tab focused for mobile-watching owner.
    try:
        page.bring_to_front()
    except Exception:
        pass

    deadline = time.time() + wait
    last_banner = 0.0
    while time.time() < deadline:
        try:
            url = page.url or ""
        except Exception:
            url = ""
        body = ""
        try:
            body = page.locator("body").inner_text(timeout=1500)[:2000]
        except Exception:
            pass

        if not is_google_2fa_challenge(page, url=url, body=body):
            # Left Google challenge, or landed on a signed-in destination.
            if "accounts.google.com" not in url.lower() or _DONE_URL_RE.search(url):
                print(
                    f"ASK_OWNER_GOOGLE_2FA ({portal}) resolved — continuing",
                    flush=True,
                )
                return True
            # Still on Google but no longer a challenge screen (e.g. account home).
            if not _CHALLENGE_RE.search(f"{url}\n{body}"):
                print(
                    f"ASK_OWNER_GOOGLE_2FA ({portal}) resolved — continuing",
                    flush=True,
                )
                return True

        now = time.time()
        if now - last_banner >= 45:
            left = max(0, int(deadline - now))
            print(
                f"ASK_OWNER_GOOGLE_2FA ({portal}) still waiting — {left}s left; "
                "enter authenticator code in Chrome / approve phone prompt",
                flush=True,
            )
            last_banner = now
            try:
                page.bring_to_front()
            except Exception:
                pass

        time.sleep(max(0.5, poll))

    print(
        f"ASK_OWNER_GOOGLE_2FA ({portal}) timeout after {wait}s — challenge still open",
        flush=True,
    )
    return False


def main() -> int:
    """CLI smoke: detect challenge from URL/body args (no browser)."""
    url = sys.argv[1] if len(sys.argv) > 1 else ""
    body = sys.argv[2] if len(sys.argv) > 2 else ""
    hit = is_google_2fa_challenge(url=url, body=body)
    print(json_dumps := __import__("json").dumps({"is_2fa": hit, "url": url[:120]}))
    return 0 if True else 1


if __name__ == "__main__":
    raise SystemExit(main())
