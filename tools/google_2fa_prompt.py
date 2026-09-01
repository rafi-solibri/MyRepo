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

_CHALLENGE_RE = re.compile(
    r"2[- ]step|two[- ]step|authenticator|verification code|"
    r"enter (the |your )?(code|pin)|google prompt|"
    r"check your phone|tap yes|confirm it.?s you|"
    r"account recovery|verify it.?s you|signin/challenge|"
    r"challenge/totp|challenge/ipp|challenge/sk|/challenge/",
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
    # Password entry is NOT 2FA — /challenge/pwd must not block on owner wait.
    if re.search(r"signin/challenge/pwd|challenge/pwd", u, re.I):
        return False
    if re.search(r"enter your password|wrong password", text, re.I) and not re.search(
        r"2[- ]step|authenticator|tap yes|check your phone", text, re.I
    ):
        return False
    if "accounts.google.com" in u.lower() and _CHALLENGE_RE.search(blob):
        return True
    if re.search(r"accounts\.google\.com/.*/challenge/(?!pwd)", u, re.I):
        return True
    if _CHALLENGE_RE.search(text) and re.search(
        r"google|g-?suite|rafi\.success@gmail", text, re.I
    ):
        return True
    return False


def extract_google_2fa_match_number(page: Any = None, *, body: str = "") -> str | None:
    """Return the on-screen Google number-match digit(s) when present.

    Google sometimes shows a large 1–3 digit number to pick on the phone prompt.
    Push-only 'Tap Yes' challenges have no number — returns None.
    """
    text = body or ""
    if page is not None and not text:
        try:
            text = page.locator("body").inner_text(timeout=2000)[:2500]
        except Exception:
            text = ""
    # Explicit copy: "Enter the number … 42" / "number 42"
    m = re.search(
        r"(?:enter|choose|select|tap|match)?\s*(?:the\s+)?number\s*[#: ]?\s*(\d{1,3})\b",
        text,
        re.I,
    )
    if m:
        return m.group(1)
    if page is not None:
        # Large numeric nodes on the challenge card (avoid tiny chrome digits).
        for sel in (
            "div[data-is-numeric='true']",
            "div[jsname] span",
            "div[role='heading']",
            "h1",
            "h2",
            "strong",
        ):
            try:
                locs = page.locator(sel)
                n = min(locs.count(), 30)
            except Exception:
                continue
            for i in range(n):
                try:
                    el = locs.nth(i)
                    t = (el.inner_text(timeout=500) or "").strip()
                    if not re.fullmatch(r"\d{1,3}", t):
                        continue
                    box = el.bounding_box()
                    if box and box.get("height", 0) >= 28 and box.get("width", 0) >= 20:
                        return t
                except Exception:
                    continue
    return None


def prompt_google_2fa_in_chat(portal: str, *, wait_sec: int, detail: str = "", match_number: str | None = None) -> None:
    """Loud transcript banner so the owner can enter the phone authenticator code."""
    lines = [
        "",
        "=" * 64,
        f"ASK_OWNER_GOOGLE_2FA ({portal})",
        "=" * 64,
        "Google is asking for a 2-factor / authenticator / phone prompt code.",
    ]
    if match_number:
        lines.append(f"NUMBER TO SELECT ON YOUR PHONE: {match_number}")
        lines.append("1) Open the Google prompt on your mobile NOW.")
        lines.append(f"2) Tap the number {match_number} (not a different digit).")
        lines.append("3) Leave this Cursor chat open — the agent is waiting.")
    else:
        lines.append("1) Open Google Authenticator (or the Google phone prompt) on your mobile NOW.")
        lines.append("2) Type the 6-digit code into the focused Chrome tab (or tap Yes on the phone).")
        lines.append("3) Leave this Cursor chat open — the agent is waiting and will continue after success.")
    lines.append(f"Waiting up to {wait_sec}s for the challenge to clear…")
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
    match_number = extract_google_2fa_match_number(page)
    prompt_google_2fa_in_chat(
        portal, wait_sec=wait, detail=url, match_number=match_number
    )

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
