#!/usr/bin/env python3
"""Tests for LinkedIn restriction memory + pacing helpers."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tools.linkedin.restriction import (
    clear_restriction_memory,
    linkedin_blocked_until,
    page_looks_restricted,
    parse_restriction_lift,
    people_referrals_enabled,
    should_skip_linkedin_for_restriction,
    write_restriction_memory,
)


def test_parse_restriction_lift_pdt():
    body = (
        "Your account has been temporarily restricted due to unusually high "
        "volume of LinkedIn profile data. Your restriction will be lifted on "
        "August 30, 2026 7:43 PM PDT."
    )
    lift = parse_restriction_lift(body)
    assert lift is not None
    # 19:43 PDT = 02:43 UTC next day
    assert lift == datetime(2026, 8, 31, 2, 43, tzinfo=timezone.utc)


def test_page_looks_restricted_requires_copy():
    assert page_looks_restricted(url="https://www.linkedin.com/checkpoint/challenge/x", body="") is None
    info = page_looks_restricted(
        url="https://www.linkedin.com/checkpoint/challenge/x",
        body=(
            "Your account has been temporarily restricted. "
            "Your restriction will be lifted on August 30, 2026 7:43 PM PDT."
        ),
    )
    assert info is not None
    assert info["kind"] == "account_temporarily_restricted"
    assert info.get("lift_utc")


def test_restriction_memory_roundtrip(tmp_path: Path, monkeypatch):
    flag = tmp_path / "restr.json"
    monkeypatch.setattr("tools.linkedin.restriction.FLAG_PATH", flag)
    monkeypatch.setattr("tools.linkedin.restriction.ARTIFACT_FLAG", tmp_path / "art.json")
    clear_restriction_memory()
    future = datetime.now(timezone.utc) + timedelta(hours=2)
    write_restriction_memory(
        {
            "kind": "account_temporarily_restricted",
            "lift_utc": future.isoformat(),
            "seconds_until_lift": 7200,
            "url": "https://www.linkedin.com/checkpoint/challenge/x",
        }
    )
    assert flag.is_file()
    blocked = linkedin_blocked_until()
    assert blocked is not None
    skip = should_skip_linkedin_for_restriction()
    assert skip and skip["reason"] == "linkedin_temporarily_restricted"
    # Past lift → cleared
    past = datetime.now(timezone.utc) - timedelta(minutes=5)
    write_restriction_memory({"lift_utc": past.isoformat(), "seconds_until_lift": 0})
    assert linkedin_blocked_until() is None


def test_people_referrals_default_off(monkeypatch):
    monkeypatch.delenv("LINKEDIN_PEOPLE_REFERRALS", raising=False)
    monkeypatch.delenv("HITECHCITY_LI_PEOPLE_REFERRALS", raising=False)
    assert people_referrals_enabled() is False
    monkeypatch.setenv("HITECHCITY_LI_PEOPLE_REFERRALS", "1")
    assert people_referrals_enabled() is True


if __name__ == "__main__":
    import os
    import tempfile

    test_parse_restriction_lift_pdt()
    test_page_looks_restricted_requires_copy()
    from tools.linkedin import restriction as r

    with tempfile.TemporaryDirectory() as d:
        old_f, old_a = r.FLAG_PATH, r.ARTIFACT_FLAG
        r.FLAG_PATH = Path(d) / "restr.json"
        r.ARTIFACT_FLAG = Path(d) / "art.json"
        try:
            clear_restriction_memory()
            future = datetime.now(timezone.utc) + timedelta(hours=2)
            write_restriction_memory(
                {"lift_utc": future.isoformat(), "seconds_until_lift": 7200}
            )
            assert linkedin_blocked_until() is not None
            assert should_skip_linkedin_for_restriction() is not None
            past = datetime.now(timezone.utc) - timedelta(minutes=5)
            write_restriction_memory({"lift_utc": past.isoformat(), "seconds_until_lift": 0})
            assert linkedin_blocked_until() is None
        finally:
            r.FLAG_PATH, r.ARTIFACT_FLAG = old_f, old_a
    os.environ.pop("LINKEDIN_PEOPLE_REFERRALS", None)
    os.environ.pop("HITECHCITY_LI_PEOPLE_REFERRALS", None)
    assert people_referrals_enabled() is False
    os.environ["HITECHCITY_LI_PEOPLE_REFERRALS"] = "1"
    assert people_referrals_enabled() is True
    print("ok")
