#!/usr/bin/env python3
"""Unit tests for cross-portal auth freshness helpers (no Chrome)."""
from __future__ import annotations

import base64
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.portal_auth_freshness import (  # noqa: E402
    foundit_jwt_from_mssoat,
    foundit_meta,
    generic_meta,
    indeed_meta,
    jwt_exp,
)


def _jwt(exp: int) -> str:
    header = base64.urlsafe_b64encode(b'{"alg":"none"}').decode().rstrip("=")
    payload = base64.urlsafe_b64encode(
        json.dumps({"exp": exp}).encode()
    ).decode().rstrip("=")
    return f"{header}.{payload}.sig"


def test_indeed_expired():
    now = 1788240995.0  # 2026-09-01
    m = indeed_meta(
        {
            "__Secure-PassportAuthProxy-OauthExpires": "1786004609",
            "__Secure-PassportAuthProxy-BearerToken": _jwt(1786004609),
        },
        now=now,
    )
    assert m["expired"] is True
    assert m["ok"] is False
    assert m["reason"] == "indeed_session_expired"


def test_indeed_fresh():
    now = 1788240995.0
    m = indeed_meta(
        {
            "__Secure-PassportAuthProxy-OauthExpires": "1893456000",
            "__Secure-PassportAuthProxy-BearerToken": _jwt(1893456000),
        },
        now=now,
    )
    assert m["expired"] is False
    assert m["ok"] is True


def test_foundit_mssoat_jwt_exp():
    jwt = _jwt(1786004609)
    # Foundit stores base64(jwt::…)
    blob = base64.b64encode(f"{jwt}::extra".encode()).decode()
    assert foundit_jwt_from_mssoat(blob) == jwt
    m = foundit_meta({"MSSOAT": blob}, now=1788240995.0)
    assert m["expired"] is True
    assert m["reason"] == "foundit_session_expired"
    fresh = foundit_meta({"MSSOAT": base64.b64encode(f"{_jwt(1893456000)}::x".encode()).decode()}, now=1788240995.0)
    assert fresh["ok"] is True


def test_generic_needs_value():
    g = generic_meta("linkedin", {"li_at": "abc"})
    assert g["ok"] is True
    g2 = generic_meta("linkedin", {})
    assert g2["ok"] is False


def test_jwt_exp_helper():
    assert jwt_exp(_jwt(100)) == 100
    assert jwt_exp("not-a-jwt") is None


if __name__ == "__main__":
    test_indeed_expired()
    test_indeed_fresh()
    test_foundit_mssoat_jwt_exp()
    test_generic_needs_value()
    test_jwt_exp_helper()
    print("ok")
