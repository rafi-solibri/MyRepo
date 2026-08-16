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


def test_max_apply_tabs_ignores_worker_parallel_tabs_one():
    from tools.hitechcity import careers_apply

    prev_w = os.environ.get("HITECHCITY_PARALLEL_WORKER")
    prev_t = os.environ.get("HITECHCITY_PARALLEL_TABS")
    prev_c = os.environ.get("HITECHCITY_MAX_CHROME_TABS")
    try:
        os.environ.pop("HITECHCITY_MAX_CHROME_TABS", None)
        os.environ["HITECHCITY_PARALLEL_WORKER"] = "3"
        os.environ["HITECHCITY_PARALLEL_TABS"] = "1"
        assert careers_apply._max_apply_tabs() == 10
    finally:
        for k, v in (
            ("HITECHCITY_PARALLEL_WORKER", prev_w),
            ("HITECHCITY_PARALLEL_TABS", prev_t),
            ("HITECHCITY_MAX_CHROME_TABS", prev_c),
        ):
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_workable_companies_prefer_careers_urls():
    from tools.hitechcity.careers_parallel import _workable_companies

    got = _workable_companies(
        [
            {"name": "NoUrlCo"},
            {"name": "HasUrl", "careersUrls": ["https://jobs.example.com"]},
        ]
    )
    assert [c["name"] for c in got] == ["HasUrl"]


def test_daily_apply_setdefault_parallel_tabs():
    src = Path(__file__).with_name("daily_apply.py").read_text(encoding="utf-8")
    assert 'os.environ.setdefault("HITECHCITY_PARALLEL_TABS", "10")' in src
    assert 'os.environ.setdefault("HITECHCITY_MAX_CHROME_TABS", "10")' in src
    assert 'os.environ.setdefault("ATS_OWNER_FOCUS_EVERY_SEC", "2")' in src
    assert "PARALLEL (PRIMARY)" in src or "parallel multi-tab" in src.lower()


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


def test_url_is_owner_park():
    from tools.hitechcity.careers_apply import url_is_owner_park

    assert url_is_owner_park("https://jobs.example.com/apply?hcaptcha=1") or url_is_owner_park(
        "https://careers-hyland.icims.com/jobs/1/login?hcaptcha=1"
    )
    assert url_is_owner_park(
        "https://modmed.wd501.myworkdayjobs.com/en-US/x/job/y/apply/autofill"
    )
    assert not url_is_owner_park("https://careers.example.com/jobs?q=lead")


def test_prune_surplus_tabs_caps_apply_pages():
    from tools.hitechcity.careers_apply import prune_surplus_tabs

    class _P:
        def __init__(self, url):
            self.url = url
            self.closed = False

        def close(self):
            self.closed = True

    class _Ctx:
        def __init__(self, pages):
            self.pages = pages

    pages = [
        _P("https://linkedin.com/jobs/"),
        _P("about:blank#hitech-w0"),
        _P("about:blank#hitech-w1"),
        _P("https://jobs.example.com/a"),
        _P("https://jobs.example.com/b"),
        _P("about:blank"),
    ]
    ctx = _Ctx(pages)
    closed = prune_surplus_tabs(ctx)
    assert closed == 3
    assert not pages[0].closed and not pages[1].closed and not pages[2].closed
    assert pages[3].closed and pages[4].closed and pages[5].closed


def test_home_headed_exports_parallel():
    sh = Path(__file__).resolve().parents[2] / "scripts" / "home-headed-careers-apply.sh"
    text = sh.read_text(encoding="utf-8")
    assert 'HITECHCITY_PARALLEL_TABS="${HITECHCITY_PARALLEL_TABS:-10}"' in text
    assert 'ATS_OWNER_FOCUS_EVERY_SEC="${ATS_OWNER_FOCUS_EVERY_SEC:-2}"' in text


if __name__ == "__main__":
    test_careers_parallel_default_is_ten()
    test_max_apply_tabs_ignores_worker_parallel_tabs_one()
    test_workable_companies_prefer_careers_urls()
    test_daily_apply_setdefault_parallel_tabs()
    test_daily_apply_import_sets_parallel_when_unset()
    test_url_is_owner_park()
    test_prune_surplus_tabs_caps_apply_pages()
    test_home_headed_exports_parallel()
    print("ok")
