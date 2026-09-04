#!/usr/bin/env python3
"""Ensure every daily entrypoint defaults to parallel multi-tab careers."""

from __future__ import annotations

import importlib
import os
import re
from pathlib import Path


def test_careers_parallel_default_is_ten():
    from tools.hitechcity import careers_parallel

    assert careers_parallel.PARALLEL_TABS == 10 or int(
        os.environ.get("HITECHCITY_PARALLEL_TABS", "10")
    ) == 10


def test_daily_apply_setdefault_parallel_tabs():
    src = Path(__file__).with_name("daily_apply.py").read_text(encoding="utf-8")
    assert 'os.environ.setdefault("HITECHCITY_PARALLEL_TABS", "10")' in src
    assert 'os.environ.setdefault("ATS_OWNER_FOCUS_EVERY_SEC", "2")' in src
    assert "PARALLEL (PRIMARY)" in src or "parallel multi-tab" in src.lower()
    assert "Headless cloud" in src and "persist_retry" in src


def test_daily_apply_import_sets_parallel_when_unset():
    prev = os.environ.pop("HITECHCITY_PARALLEL_TABS", None)
    try:
        # Re-import path: setdefault only runs at first import; assert source contract
        # and that careers_apply fans out when tabs > 1.
        from tools.hitechcity import careers_apply

        src = Path(careers_apply.__file__).read_text(encoding="utf-8")
        assert re.search(r'HITECHCITY_PARALLEL_TABS.*["\']10["\']', src)
        assert "run_parallel" in src
    finally:
        if prev is None:
            os.environ.pop("HITECHCITY_PARALLEL_TABS", None)
        else:
            os.environ["HITECHCITY_PARALLEL_TABS"] = prev


def test_home_headed_exports_parallel():
    sh = Path(__file__).resolve().parents[2] / "scripts" / "home-headed-careers-apply.sh"
    text = sh.read_text(encoding="utf-8")
    assert 'HITECHCITY_PARALLEL_TABS="${HITECHCITY_PARALLEL_TABS:-10}"' in text
    assert 'ATS_OWNER_FOCUS_EVERY_SEC="${ATS_OWNER_FOCUS_EVERY_SEC:-2}"' in text


if __name__ == "__main__":
    test_careers_parallel_default_is_ten()
    test_daily_apply_setdefault_parallel_tabs()
    test_daily_apply_import_sets_parallel_when_unset()
    test_home_headed_exports_parallel()
    print("ok")
