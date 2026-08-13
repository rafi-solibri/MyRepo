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
    print("ok")
