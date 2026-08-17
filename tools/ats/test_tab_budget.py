#!/usr/bin/env python3
"""Unit checks for the 10-tab Chrome budget (no live browser)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.ats import tab_budget as tb


class _FakePage:
    def __init__(self, tag=None, *, dead=False):
        self.tag = tag
        self.dead = dead
        self.closed = False
        self.url = "about:blank"

    def evaluate(self, js):
        if self.dead:
            raise RuntimeError("closed")
        if "window.__HTW" in js and "=" not in js.split("=>", 1)[-1]:
            return self.tag
        if "__HTW =" in js.replace(" ", ""):
            try:
                self.tag = int(js.rsplit("=", 1)[-1].split(";")[0].strip())
            except Exception:
                self.tag = 0
            return None
        return self.tag

    def close(self):
        self.closed = True
        self.dead = True


class _FakeContext:
    def __init__(self, pages):
        self.pages = list(pages)


def test_max_tabs_hard_capped():
    key = "HITECH" + "CITY_PARALLEL_TABS"
    prev = os.environ.get(key)
    try:
        os.environ[key] = "99"
        assert tb.max_parallel_tabs() == 10
        os.environ[key] = "3"
        assert tb.max_parallel_tabs() == 3
        os.environ[key] = "0"
        assert tb.max_parallel_tabs() == 1
    finally:
        if prev is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = prev


def test_prune_closes_untagged_first():
    tagged = [_FakePage(i) for i in range(10)]
    extra = _FakePage(None)
    ctx = _FakeContext(tagged + [extra])
    closed = tb.prune_extra_pages(ctx, keep=set(tagged), max_tabs=10)
    assert closed == 1
    assert extra.closed is True
    assert all(not p.closed for p in tagged)


def test_close_other_pages_keeps_sibling_workers():
    key = "HITECH" + "CITY_PARALLEL_WORKER"
    os.environ[key] = "2"
    try:
        mine = _FakePage(2)
        sibling = _FakePage(3)
        popup = _FakePage(None)
        ctx = _FakeContext([mine, sibling, popup])
        closed = tb.close_other_pages(ctx, mine)
        assert closed == 1
        assert popup.closed is True
        assert sibling.closed is False
        assert mine.closed is False
    finally:
        os.environ.pop(key, None)


if __name__ == "__main__":
    test_max_tabs_hard_capped()
    test_prune_closes_untagged_first()
    test_close_other_pages_keeps_sibling_workers()
    print("tools/ats/test_tab_budget.py OK")
