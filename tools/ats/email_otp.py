#!/usr/bin/env python3
"""Read ATS email OTPs from the owner's mailbox and fill them on the apply page.

Primary path: Gmail in the same Chrome CDP profile (Google session already used
for LinkedIn SSO). Optional IMAP path when ``GMAIL_APP_PASSWORD`` (or
``GOOGLE_APP_PASSWORD``) is set.

Never logs the full OTP — only length / source. Never invents codes.
"""

from __future__ import annotations

import email
import email.header
import email.utils
import imaplib
import os
import re
import sys
import time
from email.message import Message
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# 4–8 digit codes; prefer 6. Exclude common false positives (years, phone scraps).
_CODE_NEAR = re.compile(
    r"(?:verification\s*code|one[-\s]?time\s*(?:pass(?:code|word)|code)|"
    r"security\s*code|otp|passcode|enter(?:\s+the)?\s+code|"
    r"code(?:\s+is|\s*:)|confirm(?:ation)?\s+code)"
    r"[^\d]{0,40}(\d{4,8})",
    re.I,
)
_BARE_CODE = re.compile(r"\b(\d{6})\b")
_YEARISH = re.compile(r"^(19|20)\d{2}$")
_LOCK_PATH = Path(os.environ.get("ATS_GMAIL_OTP_LOCK", "/tmp/ats-gmail-otp.lock"))
# Cross-process: when Gmail CDP shows Sign-in and no IMAP app password is set,
# parallel careers workers must not each burn the full ATS_EMAIL_OTP_WAIT_SEC.
_GMAIL_LOGIN_FLAG = Path(
    os.environ.get("ATS_GMAIL_LOGIN_FLAG", "/tmp/ats-gmail-otp-login-required")
)

_GMAIL_SEARCH = (
    "newer_than:1d (verification OR OTP OR \"one-time\" OR \"security code\" "
    "OR \"confirm your identity\" OR passcode OR \"verification code\")"
)


def reset_gmail_login_flag() -> None:
    """Clear the per-run Gmail Sign-in cache (call once at daily apply start)."""
    try:
        _GMAIL_LOGIN_FLAG.unlink(missing_ok=True)
    except Exception:
        pass


def gmail_session_known_dead() -> bool:
    try:
        return _GMAIL_LOGIN_FLAG.exists()
    except Exception:
        return False


def mark_gmail_login_required() -> None:
    try:
        _GMAIL_LOGIN_FLAG.parent.mkdir(parents=True, exist_ok=True)
        _GMAIL_LOGIN_FLAG.write_text("1", encoding="utf-8")
    except Exception:
        pass


def mailbox_unavailable_for_otp() -> bool:
    """True when Gmail CDP needs Sign-in and no IMAP app password is configured."""
    return gmail_session_known_dead() and not mailbox_app_password()


def mailbox_user() -> str:
    return (
        os.environ.get("GMAIL_IMAP_USER")
        or os.environ.get("APPLY_EMAIL")
        or os.environ.get("LINKEDIN_EMAIL")
        or os.environ.get("GOOGLE_EMAIL")
        or ""
    ).strip()


def mailbox_app_password() -> str:
    return (
        os.environ.get("GMAIL_APP_PASSWORD")
        or os.environ.get("GOOGLE_APP_PASSWORD")
        or os.environ.get("GMAIL_IMAP_PASSWORD")
        or ""
    ).strip().replace(" ", "")


def extract_otp_candidates(text: str | None) -> list[str]:
    """Return ranked OTP candidates from email subject/body text (no secrets logged)."""
    blob = text or ""
    found: list[str] = []
    seen: set[str] = set()

    def _add(code: str) -> None:
        c = (code or "").strip()
        if not c or c in seen:
            return
        if _YEARISH.match(c):
            return
        if len(c) < 4 or len(c) > 8:
            return
        seen.add(c)
        found.append(c)

    for m in _CODE_NEAR.finditer(blob):
        _add(m.group(1))
    for m in _BARE_CODE.finditer(blob):
        _add(m.group(1))
    # Prefer 6-digit, then longer, then shorter.
    found.sort(key=lambda c: (0 if len(c) == 6 else 1 if len(c) > 6 else 2, -len(c)))
    return found


def _decode_header(raw: str | None) -> str:
    if not raw:
        return ""
    parts = []
    for chunk, enc in email.header.decode_header(raw):
        if isinstance(chunk, bytes):
            parts.append(chunk.decode(enc or "utf-8", errors="replace"))
        else:
            parts.append(chunk)
    return " ".join(parts)


def _message_text(msg: Message) -> str:
    chunks: list[str] = [_decode_header(msg.get("Subject"))]
    if msg.is_multipart():
        for part in msg.walk():
            ctype = (part.get_content_type() or "").lower()
            if ctype not in ("text/plain", "text/html"):
                continue
            try:
                payload = part.get_payload(decode=True) or b""
                charset = part.get_content_charset() or "utf-8"
                text = payload.decode(charset, errors="replace")
            except Exception:
                continue
            if ctype == "text/html":
                text = re.sub(r"<[^>]+>", " ", text)
            chunks.append(text)
    else:
        try:
            payload = msg.get_payload(decode=True) or b""
            charset = msg.get_content_charset() or "utf-8"
            chunks.append(payload.decode(charset, errors="replace"))
        except Exception:
            pass
    return "\n".join(chunks)


def fetch_otp_via_imap(*, after_epoch: float | None = None, timeout_s: float = 45) -> str | None:
    """Poll Gmail IMAP for a fresh verification code. Requires app password."""
    user = mailbox_user()
    password = mailbox_app_password()
    if not user or not password:
        return None
    host = os.environ.get("GMAIL_IMAP_HOST", "imap.gmail.com")
    deadline = time.time() + max(5.0, timeout_s)
    after = after_epoch or (time.time() - 900)
    while time.time() < deadline:
        try:
            client = imaplib.IMAP4_SSL(host, 993)
            try:
                client.login(user, password)
                client.select("INBOX")
                # Recent messages only — UID SEARCH SINCE uses date not time.
                typ, data = client.search(None, "UNSEEN")
                if typ != "OK" or not data or not data[0]:
                    typ, data = client.search(None, "ALL")
                ids = (data[0] or b"").split()
                for uid in reversed(ids[-25:]):
                    typ, fetched = client.fetch(uid, "(RFC822)")
                    if typ != "OK" or not fetched:
                        continue
                    raw = fetched[0][1]
                    msg = email.message_from_bytes(raw)
                    # Skip stale mail when Date is parseable.
                    date_tuple = email.utils.parsedate_tz(msg.get("Date") or "")
                    if date_tuple:
                        msg_ts = email.utils.mktime_tz(date_tuple)
                        if msg_ts < after - 30:
                            continue
                    text = _message_text(msg)
                    if not re.search(
                        r"verification|otp|one[-\s]?time|passcode|confirm your identity|security code",
                        text,
                        re.I,
                    ):
                        continue
                    codes = extract_otp_candidates(text)
                    if codes:
                        print(f"email_otp=imap_hit len={len(codes[0])}", flush=True)
                        return codes[0]
            finally:
                try:
                    client.logout()
                except Exception:
                    pass
        except Exception as exc:
            print(f"email_otp=imap_err {type(exc).__name__}", flush=True)
        time.sleep(3.0)
    print("email_otp=imap_miss", flush=True)
    return None


def _with_gmail_lock(fn):
    """Serialize Gmail tab access across parallel careers workers."""
    try:
        import fcntl
    except Exception:
        return fn()
    _LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_LOCK_PATH, "a+", encoding="utf-8") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            return fn()
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def fetch_otp_via_gmail_tab(page, *, after_epoch: float | None = None, timeout_s: float = 55) -> str | None:
    """Open Gmail in a new CDP tab, scrape recent OTP mail, close the tab."""
    if mailbox_unavailable_for_otp():
        print("email_otp=gmail_login_required_cached", flush=True)
        return None
    try:
        context = page.context
    except Exception:
        return None

    def _run() -> str | None:
        gmail = None
        try:
            gmail = context.new_page()
        except Exception as exc:
            print(f"email_otp=gmail_tab_open_fail {type(exc).__name__}", flush=True)
            return None
        try:
            q = _GMAIL_SEARCH
            # Prefer basic HTML — simpler DOM for scraping.
            basic = (
                "https://mail.google.com/mail/u/0/h/"
                f"?s=q&q={q.replace(' ', '+').replace('\"', '%22')}"
            )
            modern = (
                "https://mail.google.com/mail/u/0/#search/"
                + q.replace(" ", "+").replace('"', "%22")
            )
            for url in (basic, modern):
                try:
                    gmail.goto(url, wait_until="domcontentloaded", timeout=45000)
                except Exception:
                    continue
                time.sleep(2.2)
                cur = (getattr(gmail, "url", "") or "").lower()
                if "accounts.google.com" in cur or "/signin" in cur:
                    mark_gmail_login_required()
                    print("email_otp=gmail_login_required", flush=True)
                    return None
                # Collect page text (list view or thread).
                try:
                    blob = gmail.locator("body").inner_text(timeout=8000) or ""
                except Exception:
                    blob = ""
                if re.search(r"sign in|couldn't sign you in", blob, re.I) and not re.search(
                    r"inbox|primary|search", blob, re.I
                ):
                    mark_gmail_login_required()
                    print("email_otp=gmail_login_required", flush=True)
                    return None
                codes = extract_otp_candidates(blob)
                if codes:
                    print(f"email_otp=gmail_hit len={len(codes[0])} via=list", flush=True)
                    return codes[0]
                # Try opening the first result row.
                clicked = False
                for sel in (
                    "table.th tr.zA",
                    "tr.zA",
                    "div[role='main'] tr",
                    "div[role='listitem']",
                    "table.N tr",
                    "a[href*='th=']",
                ):
                    try:
                        loc = gmail.locator(sel).first
                        if loc.count() and loc.is_visible():
                            loc.click(timeout=3000)
                            clicked = True
                            time.sleep(1.8)
                            break
                    except Exception:
                        continue
                if clicked:
                    try:
                        blob = gmail.locator("body").inner_text(timeout=8000) or ""
                    except Exception:
                        blob = ""
                    codes = extract_otp_candidates(blob)
                    if codes:
                        print(f"email_otp=gmail_hit len={len(codes[0])} via=thread", flush=True)
                        return codes[0]
            print("email_otp=gmail_miss", flush=True)
            return None
        finally:
            try:
                gmail.close()
            except Exception:
                pass

    # Bound wait: lock + scrape.
    start = time.time()
    result = _with_gmail_lock(_run)
    _ = after_epoch, timeout_s, start  # reserved for future tighter freshness filters
    return result


def fetch_email_otp(page=None, *, after_epoch: float | None = None, timeout_s: float = 55) -> str | None:
    """IMAP first (if configured), else Gmail CDP tab."""
    code = fetch_otp_via_imap(after_epoch=after_epoch, timeout_s=min(20.0, timeout_s))
    if code:
        return code
    if page is None:
        return None
    return fetch_otp_via_gmail_tab(page, after_epoch=after_epoch, timeout_s=timeout_s)


def fill_otp_fields(page, code: str) -> bool:
    """Type the OTP into visible code inputs on the ATS page."""
    if not code:
        return False
    selectors = (
        'input[autocomplete="one-time-code"]',
        'input[inputmode="numeric"]',
        'input[name*="otp" i]',
        'input[name*="code" i]',
        'input[id*="otp" i]',
        'input[id*="code" i]',
        'input[aria-label*="code" i]',
        'input[aria-label*="otp" i]',
        'input[placeholder*="code" i]',
        'input[placeholder*="otp" i]',
        'input[type="tel"]',
        'input[type="text"]',
        'input[type="number"]',
    )
    filled = False
    for sel in selectors:
        try:
            loc = page.locator(sel)
            n = min(loc.count(), 6)
            for i in range(n):
                el = loc.nth(i)
                try:
                    if not el.is_visible():
                        continue
                    name = (
                        (el.get_attribute("name") or "")
                        + " "
                        + (el.get_attribute("id") or "")
                        + " "
                        + (el.get_attribute("aria-label") or "")
                        + " "
                        + (el.get_attribute("placeholder") or "")
                        + " "
                        + (el.get_attribute("autocomplete") or "")
                    ).lower()
                    # Skip password / email / phone unless clearly an OTP field.
                    if re.search(r"password|email|phone|mobile|search", name) and not re.search(
                        r"otp|code|one-time|verification", name
                    ):
                        continue
                    if sel in ('input[type="text"]', 'input[type="tel"]', 'input[type="number"]'):
                        if not re.search(
                            r"otp|code|one-time|verification|passcode|confirm",
                            name,
                        ) and "one-time-code" not in (el.get_attribute("autocomplete") or ""):
                            # On Oracle Confirm Your Identity the lone text box is the code.
                            body = ""
                            try:
                                body = page.locator("body").inner_text(timeout=1500) or ""
                            except Exception:
                                pass
                            if not re.search(r"confirm your identity|verification code", body, re.I):
                                continue
                    el.click(timeout=2000)
                    try:
                        el.fill(code)
                    except Exception:
                        el.fill("")
                        el.type(code, delay=40)
                    filled = True
                    break
                except Exception:
                    continue
            if filled:
                break
        except Exception:
            continue
    return filled


def submit_otp_form(page) -> bool:
    labels = (
        "Verify",
        "Verify email",
        "Confirm",
        "Continue",
        "Submit",
        "Next",
        "Validate",
    )
    for name in labels:
        try:
            btn = page.get_by_role("button", name=re.compile(rf"^{re.escape(name)}$", re.I))
            for i in range(min(btn.count(), 3)):
                b = btn.nth(i)
                if b.is_visible() and b.is_enabled():
                    b.click(timeout=3000, force=True)
                    return True
        except Exception:
            continue
        try:
            loc = page.locator(f"button:has-text('{name}'), input[type='submit'][value*='{name}' i]")
            if loc.count() and loc.first.is_visible():
                loc.first.click(timeout=3000, force=True)
                return True
        except Exception:
            continue
    try:
        page.keyboard.press("Enter")
        return True
    except Exception:
        return False


_OTP_WALL_RE = re.compile(
    r"confirm your identity|"
    r"verification code was sent|"
    r"enter (the|your) (verification |one[- ]time )?code|"
    r"type the code into the field|"
    r"one[- ]time (pass(code|word)|code)|"
    r"we (just )?sent (you )?(a |an )?(code|otp)|"
    r"check your (email|inbox).{0,40}(code|otp)",
    re.I,
)


def page_shows_otp_wall(page) -> bool:
    try:
        text = page.locator("body").inner_text(timeout=4000) or ""
    except Exception:
        return False
    return bool(_OTP_WALL_RE.search(text))


def otp_wall_still_present(page) -> bool:
    try:
        return page_shows_otp_wall(page)
    except Exception:
        return True


def try_clear_email_otp(page, *, wait_s: float | None = None) -> bool:
    """When an email OTP gate is showing, read mailbox + fill. True if gate cleared."""
    if os.environ.get("ATS_EMAIL_OTP", "1").strip() in ("0", "false", "no"):
        print("email_otp=disabled", flush=True)
        return False
    try:
        if not page_shows_otp_wall(page):
            return False
    except Exception:
        return False

    budget = wait_s
    if budget is None:
        try:
            budget = float(os.environ.get("ATS_EMAIL_OTP_WAIT_SEC", "60"))
        except Exception:
            budget = 60.0
    # Overnight / owner-asleep: still try mailbox (no human needed) but keep budget modest.
    if os.environ.get("HITECHCITY_OWNER_ASLEEP", "").strip() in ("1", "true", "yes") or Path(
        "/tmp/hitechcity-owner-asleep"
    ).exists():
        budget = min(budget, float(os.environ.get("ATS_EMAIL_OTP_ASLEEP_WAIT_SEC", "45")))

    # Fast-fail: prior probe already saw Gmail Sign-in and IMAP is not configured.
    # Do not burn ATS_EMAIL_OTP_WAIT_SEC × parallel workers on Oracle OTP walls.
    if mailbox_unavailable_for_otp():
        print("email_otp=gmail_login_required_abort", flush=True)
        return False

    sent_after = time.time() - 30
    print(f"email_otp=start wait={int(budget)}s", flush=True)
    deadline = time.time() + max(8.0, budget)
    attempt = 0
    while time.time() < deadline:
        attempt += 1
        code = fetch_email_otp(page, after_epoch=sent_after, timeout_s=min(25.0, deadline - time.time()))
        if not code:
            if mailbox_unavailable_for_otp():
                print("email_otp=gmail_login_required_abort", flush=True)
                return False
            time.sleep(3.0)
            continue
        if not fill_otp_fields(page, code):
            print("email_otp=fill_miss", flush=True)
            time.sleep(2.0)
            continue
        submit_otp_form(page)
        time.sleep(2.0)
        if not otp_wall_still_present(page):
            print(f"email_otp=cleared attempt={attempt}", flush=True)
            return True
        print(f"email_otp=still_on_gate attempt={attempt}", flush=True)
        time.sleep(2.5)
    print("email_otp=timeout", flush=True)
    return False
