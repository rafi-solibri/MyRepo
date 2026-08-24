#!/usr/bin/env python3
"""Shared safety gates for LinkedIn automation.

The LinkedIn account can be temporarily restricted when daily jobs browse too
many job/profile pages. Entry points should call this module before opening
LinkedIn so scheduled runs fail closed during a cooldown.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "automation-prompts" / "linkedin-safety.json"


@dataclass
class PauseStatus:
    active: bool
    reason: str = ""
    pause_until_utc: str | None = None
    seconds_remaining: int | None = None
    source: str = ""


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def parse_utc(value: str | None) -> datetime | None:
    """Parse an ISO UTC timestamp into an aware datetime."""
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text())


def pause_status(now: datetime | None = None, env: dict[str, str] | None = None) -> PauseStatus:
    """Return whether LinkedIn automation should be paused right now."""
    src_env = env if env is not None else os.environ
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    current = current.astimezone(timezone.utc)

    if _truthy(src_env.get("LINKEDIN_DISABLE_AUTOMATION")):
        return PauseStatus(
            active=True,
            reason=src_env.get("LINKEDIN_DISABLE_REASON")
            or "LINKEDIN_DISABLE_AUTOMATION is set",
            source="env:LINKEDIN_DISABLE_AUTOMATION",
        )

    cfg = load_config()
    until_raw = src_env.get("LINKEDIN_PAUSE_UNTIL_UTC") or str(
        cfg.get("pauseUntilUtc") or ""
    )
    until = parse_utc(until_raw) if until_raw else None
    if until and current < until:
        remaining = max(0, int((until - current).total_seconds()))
        return PauseStatus(
            active=True,
            reason=src_env.get("LINKEDIN_PAUSE_REASON")
            or str(cfg.get("reason") or "LinkedIn safety pause is active"),
            pause_until_utc=until.isoformat().replace("+00:00", "Z"),
            seconds_remaining=remaining,
            source=(
                "env:LINKEDIN_PAUSE_UNTIL_UTC"
                if src_env.get("LINKEDIN_PAUSE_UNTIL_UTC")
                else str(CONFIG_PATH.relative_to(ROOT))
            ),
        )

    return PauseStatus(active=False, source="none")


def safe_int(default_key: str, fallback: int) -> int:
    cfg = load_config().get("safeDefaults") or {}
    try:
        return int(cfg.get(default_key, fallback))
    except (TypeError, ValueError):
        return fallback


def main() -> int:
    parser = argparse.ArgumentParser(description="Check LinkedIn automation safety pause")
    parser.add_argument("--check", action="store_true", help="exit 20 when paused")
    args = parser.parse_args()
    status = pause_status()
    print(json.dumps(asdict(status), indent=2))
    if args.check and status.active:
        return 20
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
