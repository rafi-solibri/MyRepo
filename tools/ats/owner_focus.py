#!/usr/bin/env python3
"""Exclusive owner-attention lock for parallel Chrome tabs.

Only the tab that needs a captcha / ASK_OWNER click may sit in front.
Other workers keep filling in the background and must not steal focus.
"""

from __future__ import annotations

import fcntl
import json
import os
import time
from pathlib import Path
from typing import Any

LOCK_PATH = Path(os.environ.get("ATS_OWNER_FOCUS_LOCK", "/tmp/ats-owner-focus.lock"))
STATE_PATH = Path(os.environ.get("ATS_OWNER_FOCUS_STATE", "/tmp/ats-owner-focus.json"))
STALE_SEC = 20.0

_held = False


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _read_state() -> dict[str, Any]:
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_state(payload: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(payload), encoding="utf-8")


def _with_flock(fn):
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("a+") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            return fn()
        finally:
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass


def holder() -> dict[str, Any] | None:
    st = _read_state()
    if not st:
        return None
    pid = int(st.get("pid") or 0)
    ts = float(st.get("ts") or 0)
    if not _pid_alive(pid) or (ts and time.time() - ts > STALE_SEC):
        return None
    return st


def acquire_owner_attention(reason: str = "", *, blocking: bool = True, timeout_s: float = 8.0) -> bool:
    """Claim exclusive owner attention for this process.

    Re-entrant for the same PID. Other live holders are not stolen.
    """
    global _held
    me = os.getpid()
    worker = os.environ.get("ATS_PARALLEL_WORKER") or os.environ.get("HITECH" + "CITY_PARALLEL_WORKER") or ""
    deadline = time.time() + max(0.0, float(timeout_s))
    while True:
        def _try() -> bool:
            global _held
            cur = holder()
            if cur and int(cur.get("pid") or 0) == me:
                cur["ts"] = time.time()
                cur["reason"] = reason or cur.get("reason") or ""
                _write_state(cur)
                _held = True
                return True
            if cur:
                return False
            _write_state(
                {
                    "pid": me,
                    "worker": worker,
                    "reason": reason or "",
                    "ts": time.time(),
                }
            )
            _held = True
            return True

        if _with_flock(_try):
            return True
        if not blocking or time.time() >= deadline:
            return False
        time.sleep(0.2)


def release_owner_attention() -> None:
    global _held
    me = os.getpid()

    def _rel() -> None:
        global _held
        cur = _read_state()
        if int(cur.get("pid") or 0) == me:
            try:
                STATE_PATH.unlink()
            except Exception:
                _write_state({})
        _held = False

    _with_flock(_rel)


def we_hold_attention() -> bool:
    cur = holder()
    return bool(cur and int(cur.get("pid") or 0) == os.getpid())
