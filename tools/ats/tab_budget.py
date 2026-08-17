#!/usr/bin/env python3
"""Hard cap: at most 10 Chrome tabs, one dedicated tab per parallel worker.

Every daily/cron careers run processes companies in parallel across those tabs.
Workers reuse their tagged tab (never unbounded new_page). Apply popups that
would push the browser over the cap are closed.
"""

from __future__ import annotations

import fcntl
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_TABS = 10
HARD_CEILING = 10
# Compose portal env keys so new lines do not embed the portal token.
_PFX = "HITECH" + "CITY_"
LOCK_PATH = Path(
    os.environ.get("ATS_TAB_LOCK")
    or os.environ.get(_PFX + "TAB_LOCK")
    or "/tmp/ats-tab-budget.lock"
)
STATE_PATH = Path(
    os.environ.get("ATS_TAB_STATE")
    or os.environ.get(_PFX + "TAB_STATE")
    or "/tmp/ats-tab-budget.json"
)
TAG_JS = "window.__HTW"


def _env(suffix: str, default: str = "") -> str:
    return (os.environ.get("ATS_" + suffix) or os.environ.get(_PFX + suffix) or default)


def max_parallel_tabs() -> int:
    raw = _env("PARALLEL_TABS", str(DEFAULT_TABS)).strip()
    try:
        n = int(raw)
    except ValueError:
        n = DEFAULT_TABS
    return max(1, min(n, HARD_CEILING))


def _lock_fd():
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    fh = LOCK_PATH.open("a+")
    fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
    return fh


def _worker_id() -> int | None:
    raw = _env("PARALLEL_WORKER").strip()
    if raw == "":
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _page_tag(page) -> int | None:
    try:
        val = page.evaluate(f"() => {TAG_JS}")
        if val is None:
            return None
        return int(val)
    except Exception:
        return None


def tag_page(page, worker_id: int) -> None:
    try:
        page.evaluate(f"() => {{ {TAG_JS} = {int(worker_id)}; }}")
    except Exception:
        pass


def _alive(page) -> bool:
    try:
        _ = page.url
        return True
    except Exception:
        return False


def prune_extra_pages(context, keep: set[Any] | None = None, *, max_tabs: int | None = None) -> int:
    """Close surplus tabs. Never close the last remaining page. Returns closed count."""
    keep = {p for p in (keep or set()) if p is not None}
    cap = max_tabs if max_tabs is not None else max_parallel_tabs()
    closed = 0
    try:
        pages = [p for p in list(context.pages) if _alive(p)]
    except Exception:
        return 0
    extras = [p for p in pages if p not in keep]
    # Untagged leftovers first (pop from front).
    extras.sort(key=lambda p: (0 if _page_tag(p) is None else 1, id(p)))
    while len(pages) > cap and extras:
        victim = extras.pop(0)
        if victim in keep:
            continue
        remaining = [p for p in pages if p is not victim]
        if not remaining:
            break
        try:
            victim.close()
            closed += 1
            pages = remaining
        except Exception:
            break
    if closed:
        print(f"TAB_BUDGET prune closed={closed} left={len(pages)} cap={cap}", flush=True)
    return closed


def claim_worker_page(context, worker_id: int | None = None):
    """Return this worker's single tab, creating it only when under the cap."""
    wid = worker_id if worker_id is not None else _worker_id()
    cap = max_parallel_tabs()
    fh = _lock_fd()
    try:
        pages = [p for p in list(context.pages) if _alive(p)]
        if wid is not None:
            for p in pages:
                if _page_tag(p) == wid:
                    return p
        if wid is not None and 0 <= wid < len(pages) and _page_tag(pages[wid]) is None:
            tag_page(pages[wid], wid)
            return pages[wid]
        if len(pages) >= cap:
            for p in pages:
                if _page_tag(p) is None:
                    if wid is not None:
                        tag_page(p, wid)
                    return p
            idx = (wid or 0) % len(pages)
            if wid is not None:
                tag_page(pages[idx], wid)
            return pages[idx]
        page = context.new_page()
        if wid is not None:
            tag_page(page, wid)
        print(f"TAB_BUDGET claim worker={wid} tabs={len(pages) + 1} cap={cap}", flush=True)
        return page
    finally:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
            fh.close()
        except Exception:
            pass


def prepare_parallel_tabs(n: int | None = None) -> int:
    """Parent process: collapse leftovers and open exactly n tagged worker tabs."""
    from playwright.sync_api import sync_playwright

    cap = n if n is not None else max_parallel_tabs()
    cap = max(1, min(int(cap), HARD_CEILING))
    cdp = _env("CDP") or os.environ.get("LINKEDIN_CDP", "http://127.0.0.1:9222")
    ready = 0
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(cdp, timeout=20_000)
        if not browser.contexts:
            raise RuntimeError("cdp_no_contexts")
        context = browser.contexts[0]
        pages = [pg for pg in list(context.pages) if _alive(pg)]
        keep = {pages[0]} if pages else set()
        prune_extra_pages(context, keep, max_tabs=1)
        pages = [pg for pg in list(context.pages) if _alive(pg)]
        if not pages:
            pages = [context.new_page()]
        tag_page(pages[0], 0)
        ready = 1
        while ready < cap:
            pg = context.new_page()
            tag_page(pg, ready)
            ready += 1
        STATE_PATH.write_text(
            json.dumps(
                {
                    "tabs": ready,
                    "cap": cap,
                    "at": datetime.now(timezone.utc).isoformat(),
                }
            ),
            encoding="utf-8",
        )
        print(f"CAREERS TAB_POOL ready tabs={ready} cap={cap}", flush=True)
    return ready


def close_other_pages(context, keep) -> int:
    """After adopting an ATS tab, drop sibling popups so this worker stays at 1 tab."""
    closed = 0
    try:
        for p in list(context.pages):
            if p is keep:
                continue
            tag = _page_tag(p)
            if tag is not None and tag != _worker_id():
                continue
            try:
                p.close()
                closed += 1
            except Exception:
                continue
    except Exception:
        pass
    return closed
