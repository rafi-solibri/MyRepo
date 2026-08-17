#!/usr/bin/env python3
"""Unit checks for exclusive owner-attention lock (no browser)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["ATS_OWNER_FOCUS_LOCK"] = "/tmp/ats-owner-focus-test.lock"
os.environ["ATS_OWNER_FOCUS_STATE"] = "/tmp/ats-owner-focus-test.json"
for p in ("/tmp/ats-owner-focus-test.lock", "/tmp/ats-owner-focus-test.json"):
    Path(p).unlink(missing_ok=True)

from tools.ats.owner_focus import (
    acquire_owner_attention,
    release_owner_attention,
    we_hold_attention,
)


assert acquire_owner_attention("captcha") is True
assert we_hold_attention() is True
assert acquire_owner_attention("again") is True  # re-entrant
release_owner_attention()
assert we_hold_attention() is False
print("tools/ats/test_owner_focus.py OK")
