from __future__ import annotations

from datetime import datetime, timezone

from tools.linkedin.safety import parse_utc, pause_status


def test_parse_utc_z_suffix():
    assert parse_utc("2026-08-31T03:30:00Z") == datetime(
        2026, 8, 31, 3, 30, tzinfo=timezone.utc
    )


def test_pause_status_active_from_env():
    status = pause_status(
        now=datetime(2026, 8, 30, 3, 30, tzinfo=timezone.utc),
        env={
            "LINKEDIN_PAUSE_UNTIL_UTC": "2026-08-31T03:30:00Z",
            "LINKEDIN_PAUSE_REASON": "cooldown",
        },
    )
    assert status.active
    assert status.pause_until_utc == "2026-08-31T03:30:00Z"
    assert status.reason == "cooldown"
    assert status.seconds_remaining == 86400


def test_pause_status_inactive_after_until():
    status = pause_status(
        now=datetime(2026, 9, 1, 3, 30, tzinfo=timezone.utc),
        env={"LINKEDIN_PAUSE_UNTIL_UTC": "2026-08-31T03:30:00Z"},
    )
    assert not status.active


def test_disable_automation_env_is_active_without_until():
    status = pause_status(
        now=datetime(2026, 9, 1, 3, 30, tzinfo=timezone.utc),
        env={"LINKEDIN_DISABLE_AUTOMATION": "1", "LINKEDIN_DISABLE_REASON": "manual stop"},
    )
    assert status.active
    assert status.reason == "manual stop"
