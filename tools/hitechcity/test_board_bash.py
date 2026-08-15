#!/usr/bin/env python3
"""Tests for Windows Git Bash resolution used by board_campus_apply."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest import mock

_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from tools.hitechcity.board_campus_apply import resolve_bash


def test_resolve_bash_honors_git_bash_env():
    fake = Path(os.environ.get("LOCALAPPDATA") or ".") / "Programs" / "Git" / "bin" / "bash.exe"
    if fake.is_file():
        with mock.patch.dict(os.environ, {"GIT_BASH": str(fake)}, clear=False):
            assert resolve_bash() == str(fake)
        return
    stub = Path(__file__).resolve().parent / "_tmp_bash_stub.exe"
    try:
        stub.write_bytes(b"")
        with mock.patch.dict(os.environ, {"GIT_BASH": str(stub)}, clear=False):
            assert resolve_bash() == str(stub)
    finally:
        stub.unlink(missing_ok=True)


def test_resolve_bash_finds_git_on_this_machine():
    bash = resolve_bash()
    assert bash
    low = bash.lower().replace("/", "\\")
    assert "windowsapps" not in low
    assert not low.endswith(r"\system32\bash.exe")
    assert Path(bash).is_file()


if __name__ == "__main__":
    test_resolve_bash_honors_git_bash_env()
    test_resolve_bash_finds_git_on_this_machine()
    # Timeout must still credit applies from a fresh portal report (Indeed 2026-08-14).
    import json
    import tempfile
    from unittest import mock
    from tools.hitechcity import board_campus_apply as b

    with tempfile.TemporaryDirectory() as td:
        art = Path(td)
        (art / "indeed-daily-run.json").write_text(
            json.dumps(
                {
                    "startedAt": "2026-08-14T04:27:00+00:00",
                    "applied": [{"company": "ModMed"}, {"company": "X"}],
                    "skipped": [{}] * 3,
                    "blocked": [],
                }
            ),
            encoding="utf-8",
        )
        with mock.patch.object(b, "_artifact_dir", return_value=art):
            row = {
                "startedAt": "2026-08-14T04:27:00+00:00",
                "applied": 0,
                "blocked": 0,
                "skipped": 0,
            }
            b._harvest_portal_report(row, "indeed")
            assert row["applied"] == 2, row
            assert row["skipped"] == 3

        (art / "foundit-apply-report.json").write_text(
            json.dumps(
                {
                    "ts": "2026-08-14T05:41:29.120Z",
                    "applied": [{"jobId": "1", "company": "Virtusa"}],
                    "skipped": [{}] * 4,
                    "blocked": [],
                    "intentionalApplies": 1,
                }
            ),
            encoding="utf-8",
        )
        with mock.patch.object(b, "_artifact_dir", return_value=art):
            row = {
                "startedAt": "2026-08-14T05:41:19.099752+00:00",
                "applied": 0,
                "blocked": 0,
                "skipped": 0,
            }
            b._harvest_portal_report(row, "foundit")
            assert row.get("staleReportIgnored") is not True, row
            assert row["applied"] == 1, row
            assert row["skipped"] == 4
    print("ok")
