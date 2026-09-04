#!/usr/bin/env python3
"""LinkedIn temporary-restriction memory + safe apply pacing.

LinkedIn bans for "unusually high volume of LinkedIn profile data" are usually
triggered by people-search / profile scrapes (referrals), not Easy Apply itself.
This module:

- Detects temporary restriction pages and persists lift time
- Lets runners skip LinkedIn until the ban lifts (avoid hammering)
- Provides human-like pacing between Easy Applies
"""

from __future__ import annotations

import json
import os
import random
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

FLAG_PATH = Path(
    os.environ.get("LINKEDIN_RESTRICTION_FLAG", "/tmp/linkedin-restriction-until.json")
)
ARTIFACT_FLAG = Path("/opt/cursor/artifacts/linkedin-restriction-until.json")
# Repo-seeded flag survives fresh cloud VMs ( /tmp + artifacts are ephemeral ).
_REPO_ROOT = Path(__file__).resolve().parents[2]
REPO_FLAG = Path(
    os.environ.get(
        "LINKEDIN_RESTRICTION_REPO_FLAG",
        str(_REPO_ROOT / ".portal-sessions" / "linkedin-restriction-until.json"),
    )
)

_TZ_ALIASES = {
    "PDT": "America/Los_Angeles",
    "PST": "America/Los_Angeles",
    "EDT": "America/New_York",
    "EST": "America/New_York",
    "CDT": "America/Chicago",
    "CST": "America/Chicago",
    "MDT": "America/Denver",
    "MST": "America/Denver",
    "UTC": "UTC",
    "GMT": "UTC",
    "IST": "Asia/Kolkata",
}


def parse_restriction_lift(text: str) -> datetime | None:
    """Parse LinkedIn 'restriction will be lifted on …' into aware UTC datetime."""
    if not text:
        return None
    m = re.search(
        r"restriction will be lifted on\s+"
        r"([A-Za-z]+\s+\d{1,2},\s+\d{4}\s+\d{1,2}:\d{2}\s*[AP]M)\s*([A-Z]{2,5})",
        text,
        re.I,
    )
    if not m:
        return None
    stamp, tz_raw = m.group(1), m.group(2).upper()
    tz_name = _TZ_ALIASES.get(tz_raw)
    if not tz_name:
        fixed = {"PDT": -7, "PST": -8, "EDT": -4, "EST": -5, "IST": 5.5, "UTC": 0, "GMT": 0}
        if tz_raw not in fixed:
            return None
        tz = timezone(timedelta(hours=fixed[tz_raw]))
    else:
        tz = ZoneInfo(tz_name)
    try:
        local = datetime.strptime(stamp.strip(), "%B %d, %Y %I:%M %p").replace(tzinfo=tz)
    except ValueError:
        try:
            local = datetime.strptime(stamp.strip(), "%B %d, %Y %I:%M%p").replace(tzinfo=tz)
        except ValueError:
            return None
    return local.astimezone(timezone.utc)


def page_looks_restricted(page: Any = None, *, url: str = "", body: str = "") -> dict[str, Any] | None:
    """Return restriction info dict when page/body shows temporary account restriction."""
    u = (url or (getattr(page, "url", None) or "")).lower()
    text = body or ""
    if page is not None and not text:
        try:
            text = page.locator("body").inner_text()[:5000]
        except Exception:
            text = ""
    blob = f"{u}\n{text}"
    if not re.search(r"temporarily restricted|restriction will be lifted", blob, re.I):
        # Checkpoint alone is not enough (CAPTCHA vs restriction); require copy.
        return None
    lift = parse_restriction_lift(text)
    info: dict[str, Any] = {
        "kind": "account_temporarily_restricted",
        "url": url or getattr(page, "url", "") or "",
        "reason": "linkedin_temporarily_restricted",
    }
    now = datetime.now(timezone.utc)
    if lift is not None:
        info["lift_utc"] = lift.isoformat()
        info["seconds_until_lift"] = max(0, int((lift - now).total_seconds()))
    return info


def write_restriction_memory(info: dict[str, Any]) -> None:
    """Persist lift time so cron/CDP launch can skip LinkedIn until clear."""
    payload = {
        "writtenAt": datetime.now(timezone.utc).isoformat(),
        "lift_utc": info.get("lift_utc"),
        "seconds_until_lift": info.get("seconds_until_lift"),
        "url": info.get("url"),
        "kind": info.get("kind") or "account_temporarily_restricted",
        "hint": (
            "Do not hammer LinkedIn until lift_utc. Avoid people-search/profile scrapes. "
            "Prefer Easy Apply with pacing; disable people referrals."
        ),
    }
    raw = json.dumps(payload, indent=2)
    for path in (FLAG_PATH, ARTIFACT_FLAG, REPO_FLAG):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(raw, encoding="utf-8")
        except Exception:
            pass
    print(json.dumps({"linkedin_restriction_memory": payload}), flush=True)


def clear_restriction_memory() -> None:
    for path in (FLAG_PATH, ARTIFACT_FLAG, REPO_FLAG):
        try:
            if path.is_file():
                path.unlink()
        except Exception:
            pass


def _restriction_flag_paths() -> tuple[Path, ...]:
    """Prefer ephemeral live flags, then durable repo seed for new cloud VMs."""
    return (FLAG_PATH, ARTIFACT_FLAG, REPO_FLAG)


def read_restriction_memory() -> dict[str, Any] | None:
    for path in _restriction_flag_paths():
        try:
            if not path.is_file():
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            continue
    return None


def linkedin_blocked_until() -> datetime | None:
    """UTC lift time while a known restriction is still active; else None."""
    mem = read_restriction_memory()
    if not mem:
        return None
    lift_s = mem.get("lift_utc")
    if not lift_s:
        return None
    try:
        lift = datetime.fromisoformat(str(lift_s).replace("Z", "+00:00"))
        if lift.tzinfo is None:
            lift = lift.replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    # Small buffer after lift so LinkedIn has cleared the interstitial.
    if datetime.now(timezone.utc) + timedelta(seconds=30) < lift:
        return lift
    clear_restriction_memory()
    return None


def should_skip_linkedin_for_restriction() -> dict[str, Any] | None:
    """Non-None skip payload when LinkedIn must not be touched yet."""
    lift = linkedin_blocked_until()
    if lift is None:
        return None
    secs = max(0, int((lift - datetime.now(timezone.utc)).total_seconds()))
    return {
        "reason": "linkedin_temporarily_restricted",
        "lift_utc": lift.isoformat(),
        "seconds_until_lift": secs,
        "hint": "Wait until lift_utc; do not retry login/apply (profile-data volume ban).",
    }


def record_restriction_from_page(page: Any) -> dict[str, Any] | None:
    info = page_looks_restricted(page)
    if info:
        write_restriction_memory(info)
    return info


def pace_between_linkedin_applies() -> None:
    """Sleep between Easy Applies to stay under LinkedIn rate/abuse signals."""
    base = float(os.environ.get("LINKEDIN_APPLY_PACING_SEC", "12"))
    jitter = float(os.environ.get("LINKEDIN_APPLY_PACING_JITTER_SEC", "10"))
    # Floor so volume stays healthy but not bursty (≈3–5 applies/min max).
    wait = max(4.0, base + random.random() * max(0.0, jitter))
    print(f"LI_PACE sleep={wait:.1f}s", flush=True)
    time.sleep(wait)


def people_referrals_enabled() -> bool:
    """People-search referrals scrape profile lists — off by default after bans."""
    raw = (
        os.environ.get("LINKEDIN_PEOPLE_REFERRALS")
        or os.environ.get("HITECHCITY_LI_PEOPLE_REFERRALS")
        or "0"
    ).strip().lower()
    return raw in ("1", "true", "yes", "on")
