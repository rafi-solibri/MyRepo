#!/usr/bin/env python3
"""Chat-visible apply result notifications for every Hitech City run.

Prints a single unmistakable line per job outcome and appends JSONL under
/opt/cursor/artifacts so the agent/owner can relay SUBMITTED / NOT SUBMITTED
in chat.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

NOTIFY_PATH = Path(
    os.environ.get(
        "HITECHCITY_APPLY_CHAT_LOG",
        "/opt/cursor/artifacts/hitechcity-apply-chat.jsonl",
    )
)


def notify_application_result(
    *,
    status: str,
    company: str = "",
    role: str = "",
    reason: str = "",
    path: str = "",
    url: str = "",
) -> None:
    """Announce submitted vs not-submitted for chat / owner visibility."""
    import fcntl

    st = (status or "").strip().lower()
    company = (company or "").strip() or "?"
    role = (role or "").strip()
    reason = (reason or "").strip()
    if st == "applied":
        verdict = "SUBMITTED"
        line = f"CHAT_NOTIFY SUBMITTED | {company} | {role[:80]} | {reason or 'confirmation'}"
    elif st == "skipped" and "already" in reason.lower():
        verdict = "ALREADY_APPLIED"
        line = f"CHAT_NOTIFY ALREADY_APPLIED | {company} | {role[:80]} | {reason}"
    elif st == "skipped":
        verdict = "NOT_SUBMITTED"
        line = f"CHAT_NOTIFY NOT_SUBMITTED (skipped) | {company} | {role[:80]} | {reason}"
    else:
        verdict = "NOT_SUBMITTED"
        line = f"CHAT_NOTIFY NOT_SUBMITTED | {company} | {role[:80]} | {reason or st}"
    print(line, flush=True)
    row: dict[str, Any] = {
        "at": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "status": st,
        "company": company,
        "role": role[:160],
        "reason": reason[:200],
        "path": path,
        "url": (url or "")[:240],
        "worker": os.environ.get("HITECHCITY_PARALLEL_WORKER") or "",
    }
    try:
        NOTIFY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with NOTIFY_PATH.open("a", encoding="utf-8") as f:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            except Exception:
                pass
            try:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                f.flush()
            finally:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                except Exception:
                    pass
    except Exception:
        pass
