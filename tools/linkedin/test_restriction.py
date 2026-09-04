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
    monkeypatch.setattr("tools.linkedin.restriction.REPO_FLAG", tmp_path / "repo.json")
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
    assert (tmp_path / "repo.json").is_file()
    blocked = linkedin_blocked_until()
    assert blocked is not None
    skip = should_skip_linkedin_for_restriction()
    assert skip and skip["reason"] == "linkedin_temporarily_restricted"
    # Past lift → cleared
    past = datetime.now(timezone.utc) - timedelta(minutes=5)
    write_restriction_memory({"lift_utc": past.isoformat(), "seconds_until_lift": 0})
    assert linkedin_blocked_until() is None


def test_restriction_memory_reads_repo_seed_when_tmp_missing(tmp_path: Path, monkeypatch):
    """Fresh cloud VMs lose /tmp + artifacts; repo seed must still block until lift."""
    monkeypatch.setattr("tools.linkedin.restriction.FLAG_PATH", tmp_path / "missing-tmp.json")
    monkeypatch.setattr("tools.linkedin.restriction.ARTIFACT_FLAG", tmp_path / "missing-art.json")
    repo = tmp_path / "repo-seed.json"
    monkeypatch.setattr("tools.linkedin.restriction.REPO_FLAG", repo)
    future = datetime.now(timezone.utc) + timedelta(days=3)
    repo.write_text(
        json.dumps(
            {
                "lift_utc": future.isoformat(),
                "kind": "account_temporarily_restricted",
            }
        ),
        encoding="utf-8",
    )
    skip = should_skip_linkedin_for_restriction()
    assert skip is not None
    assert skip["reason"] == "linkedin_temporarily_restricted"


def test_people_referrals_default_off(monkeypatch):
    monkeypatch.delenv("LINKEDIN_PEOPLE_REFERRALS", raising=False)
    monkeypatch.delenv("HITECHCITY_LI_PEOPLE_REFERRALS", raising=False)
    assert people_referrals_enabled() is False
    monkeypatch.setenv("HITECHCITY_LI_PEOPLE_REFERRALS", "1")
    assert people_referrals_enabled() is True


def test_external_apply_skips_cdp_when_restricted(tmp_path: Path, monkeypatch):
    """External helper must exit 7 on restriction memory — do not open CDP."""
    from tools.linkedin import linkedin_external_apply as ext

    out = tmp_path / "external-apply-report.json"
    monkeypatch.setattr(ext, "REPORT_OUT", out)
    monkeypatch.setattr(
        ext,
        "restriction_skip_payload",
        lambda: {
            "reason": "linkedin_temporarily_restricted",
            "lift_utc": "2026-09-10T03:37:00+00:00",
            "seconds_until_lift": 100,
        },
    )
    try:
        ext.main()
        raise AssertionError("expected SystemExit 7")
    except SystemExit as exc:
        assert exc.code == 7
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["submitted"] == []
    assert data["blocked"][0]["status"] == "blocked"
    assert "linkedin_temporarily_restricted" in data["blocked"][0]["reason"]


if __name__ == "__main__":
    import os
    import tempfile

    test_parse_restriction_lift_pdt()
    test_page_looks_restricted_requires_copy()
    from tools.linkedin import restriction as r

    with tempfile.TemporaryDirectory() as d:
        old_f, old_a, old_r = r.FLAG_PATH, r.ARTIFACT_FLAG, r.REPO_FLAG
        r.FLAG_PATH = Path(d) / "restr.json"
        r.ARTIFACT_FLAG = Path(d) / "art.json"
        r.REPO_FLAG = Path(d) / "repo.json"
        try:
            clear_restriction_memory()
            future = datetime.now(timezone.utc) + timedelta(hours=2)
            write_restriction_memory(
                {"lift_utc": future.isoformat(), "seconds_until_lift": 7200}
            )
            assert linkedin_blocked_until() is not None
            assert should_skip_linkedin_for_restriction() is not None
            assert r.REPO_FLAG.is_file()
            past = datetime.now(timezone.utc) - timedelta(minutes=5)
            write_restriction_memory({"lift_utc": past.isoformat(), "seconds_until_lift": 0})
            assert linkedin_blocked_until() is None
            # Repo-only seed (fresh VM: no /tmp or artifacts)
            r.FLAG_PATH = Path(d) / "gone-tmp.json"
            r.ARTIFACT_FLAG = Path(d) / "gone-art.json"
            r.REPO_FLAG = Path(d) / "seed-only.json"
            future2 = datetime.now(timezone.utc) + timedelta(days=2)
            r.REPO_FLAG.write_text(
                json.dumps({"lift_utc": future2.isoformat()}), encoding="utf-8"
            )
            assert should_skip_linkedin_for_restriction() is not None
        finally:
            r.FLAG_PATH, r.ARTIFACT_FLAG, r.REPO_FLAG = old_f, old_a, old_r
    os.environ.pop("LINKEDIN_PEOPLE_REFERRALS", None)
    os.environ.pop("HITECHCITY_LI_PEOPLE_REFERRALS", None)
    assert people_referrals_enabled() is False
    os.environ["HITECHCITY_LI_PEOPLE_REFERRALS"] = "1"
    assert people_referrals_enabled() is True

    class _Patch:
        def setattr(self, obj, name, value):
            setattr(obj, name, value)

    test_external_apply_skips_cdp_when_restricted(Path(tempfile.mkdtemp()), _Patch())
    print("ok")
